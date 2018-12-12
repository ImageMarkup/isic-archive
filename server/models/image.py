#!/usr/bin/env python
# -*- coding: utf-8 -*-

###############################################################################
#  Copyright Kitware Inc.
#
#  Licensed under the Apache License, Version 2.0 ( the "License" );
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
###############################################################################

import itertools
import mimetypes
import os
import re

from girder import events
from girder.constants import AccessType, TokenScope
from girder.exceptions import AccessException
from girder.models.collection import Collection
from girder.models.file import File
from girder.models.item import Item
from girder.models.setting import Setting
from girder.models.token import Token
from girder.models.upload import Upload
from girder.plugins.jobs.models.job import Job
from girder.plugins.large_image.models.image_item import ImageItem
from girder.plugins.worker import utils as workerUtils

from . import segmentation_helpers
from .dataset import Dataset
from .dataset_helpers.image_metadata import addImageMetadata
from .segmentation_helpers import ScikitSegmentationHelper
from .user import User
from ..provision_utility import getAdminUser
from ..settings import PluginSettings


class Image(Item):
    def initialize(self):
        super(Image, self).initialize()

        self.prefixSearchFields = ['lowerName', 'name']

        events.bind('data.process',
                    'onSuperpixelsUpload', self.onSuperpixelsUpload)

    def createImage(self, imageDataStream, imageDataSize, originalName,
                    parentFolder, creator, dataset, batch):
        if not imageDataSize:
            # Upload().uploadFromFile will do nothing if the image is empty
            # See: https://github.com/girder/girder/issues/2773
            return

        newIsicId = Setting().get(PluginSettings.MAX_ISIC_ID) + 1
        image = self.createItem(
            name='ISIC_%07d' % newIsicId,
            creator=creator,
            folder=parentFolder,
            description=''
        )
        Setting().set(PluginSettings.MAX_ISIC_ID, newIsicId)

        image['privateMeta'] = {
            'originalFilename': originalName
        }
        image['meta'] = {
            'acquisition': {},
            'clinical': {},
            'unstructured': {},
            'unstructuredExif': {},
            'tags': [],
            'datasetId': dataset['_id'],
            'batchId': batch['_id']
        }
        image = Image().save(image)

        originalFile = Upload().uploadFromFile(
            obj=imageDataStream,
            size=imageDataSize,
            name='%s%s' % (
                image['name'],
                os.path.splitext(originalName)[1].lower()
            ),
            parentType='item',
            parent=image,
            user=creator,
            mimeType=mimetypes.guess_type(originalName)[0],
        )
        # reload image, since its 'size' has changed in the database
        image = self.load(image['_id'], force=True, exc=True)

        # this synchronously adds image['largeImage']['originalId'] and allows
        # the subsequent use of Image().originalFile and Image().imageData
        self._generateLargeimage(image, originalFile)

        self._generateSuperpixels(image)

        # TODO: copy license from dataset to image

        imageData = self.imageData(image)
        image['meta']['acquisition']['pixelsY'] = imageData.shape[0]
        image['meta']['acquisition']['pixelsX'] = imageData.shape[1]
        image = self.save(image)

        return image

    def _generateLargeimage(self, image, originalFile):
        user = User().load(image['creatorId'], force=True, exc=True)
        # Use admin user, to ensure that worker always has access
        token = Token().createToken(
            user=getAdminUser(),
            days=1,
            scope=[TokenScope.DATA_READ, TokenScope.DATA_WRITE])

        job = ImageItem().createImageItem(image, originalFile, user, token)
        return job

    def _generateSuperpixels(self, image):
        SUPERPIXEL_VERSION = 3.0

        user = User().load(image['creatorId'], force=True, exc=True)
        # Use admin user, to ensure that worker always has access
        token = Token().createToken(
            user=getAdminUser(),
            days=1,
            scope=[TokenScope.DATA_READ, TokenScope.DATA_WRITE])

        with open(os.path.join(
                os.path.dirname(__file__),
                '_generate_superpixels.py'), 'r') as scriptStream:
            script = scriptStream.read()

        title = 'superpixels v%s generation: %s' % (
            SUPERPIXEL_VERSION, image['name'])
        job = Job().createJob(
            title=title,
            type='isic_archive_superpixels',
            handler='worker_handler',
            kwargs={
                'jobInfo': None,  # will be filled after job is created
                'task': {
                    'mode': 'python',
                    'script': script,
                    'name': title,
                    'inputs': [{
                        'id': 'originalFile',
                        'type': 'string',
                        'format': 'text',
                        'target': 'filepath'
                    }, {
                        'id': 'segmentation_helpersPath',
                        'type': 'string',
                        'format': 'text',
                    }],
                    'outputs': [{
                        'id': 'superpixelsEncodedBytes',
                        'type': 'string',
                        'format': 'text',
                        'target': 'memory'
                    }]
                },
                'inputs': {
                    'originalFile': workerUtils.girderInputSpec(
                        resource=self.originalFile(image),
                        resourceType='file',
                        token=token),
                    'segmentation_helpersPath': {
                        'mode': 'inline',
                        'format': 'text',
                        'data': segmentation_helpers.__path__[0]
                    }
                },
                'outputs': {
                    'superpixelsEncodedBytes': workerUtils.girderOutputSpec(
                        parent=image,
                        token=token,
                        parentType='item',
                        name='%s_superpixels_v%s.png' %
                             (image['name'], SUPERPIXEL_VERSION),
                        reference=''
                    )
                },
                'auto_convert': False,
                'validate': False
            },
            user=user,
            public=False,
            save=True  # must save to create an _id for workerUtils.jobInfoSpec
        )
        job['kwargs']['jobInfo'] = workerUtils.jobInfoSpec(
            job,
            Job().createJobToken(job),
            logPrint=True
        )
        job['meta'] = {
            'creator': 'isic_archive',
            'task': 'generateSuperpixels',
            'imageId': image['_id'],
            'imageName': image['name'],
            'superpixelsVersion': SUPERPIXEL_VERSION
        }
        job = Job().save(job)

        Job().scheduleJob(job)
        return job

    def onSuperpixelsUpload(self, event):
        superpixelsFile = event.info['file']

        imageId = superpixelsFile.get('itemId')
        if not imageId:
            return
        image = self.load(imageId, force=True, exc=False)
        if not image:
            return

        superpixelsFileNameMatch = re.match(
            r'^%s_superpixels_v([0-9.]+)\.png' % image['name'],
            superpixelsFile['name'])
        if not superpixelsFileNameMatch:
            return

        superpixelsVersion = float(superpixelsFileNameMatch.group(1))
        superpixelsFile['superpixelVersion'] = superpixelsVersion
        # Work around an upstream Girder bug where "File().validate" sets
        #   superpixelsFile['exts'] = ['0', 'png']
        superpixelsFile = File().validate(superpixelsFile)
        superpixelsFile['exts'] = ['png']
        superpixelsFile = File().save(superpixelsFile, validate=False)

        image['superpixelsId'] = superpixelsFile['_id']
        self.save(image)

    def originalFile(self, image):
        return File().load(
            # TODO: this may fail if large_image allows "small images"
            image['largeImage']['originalId'], force=True, exc=True)

    def superpixelsFile(self, image):
        return File().load(
            image['superpixelsId'], force=True, exc=True)

    def _decodeDataFromFile(self, fileObj):
        filePath = File().getLocalFilePath(fileObj)
        # Scikit-Image is ~70ms faster at decoding image data
        data = ScikitSegmentationHelper.loadImage(filePath)
        return data

    def imageData(self, image):
        """
        Return the RGB image data associated with this image.

        :rtype: numpy.ndarray
        """
        imageFile = self.originalFile(image)
        imageData = self._decodeDataFromFile(imageFile)
        return imageData

    def superpixelsData(self, image):
        """
        Return the superpixel label data associated with this image.

        :rtype: numpy.ndarray
        """
        superpixelsFile = self.superpixelsFile(image)
        superpixelsRGBData = self._decodeDataFromFile(superpixelsFile)
        superpixelsLabelData = ScikitSegmentationHelper._RGBTounit64(
            superpixelsRGBData)
        return superpixelsLabelData

    def _findQueryFilter(self, query):
        # assumes collection has been created by provision_utility
        # TODO: cache this value
        imageCollection = Collection().findOne(
            {'name': 'Lesion Images'},
            fields={'_id': 1}
        )

        # TODO: this will also include Pre-review images; should it?
        newQuery = query.copy() if query is not None else {}
        newQuery.update({
            'baseParentId': imageCollection['_id']
        })
        return newQuery

    def find(self, query=None, **kwargs):
        imageQuery = self._findQueryFilter(query)
        return super(Image, self).find(imageQuery, **kwargs)

    def findOne(self, query=None, **kwargs):
        imageQuery = self._findQueryFilter(query)
        return super(Image, self).findOne(imageQuery, **kwargs)

    def filter(self, image, user=None, additionalKeys=None):
        output = {
            '_id': image['_id'],
            '_modelType': 'image',
            'name': image['name'],
            'created': image['created'],
            'creator': User().filterSummary(
                User().load(image['creatorId'], force=True, exc=True),
                user),
            # TODO: verify that "updated" is set correctly
            'updated': image['updated'],
            'dataset': Dataset().filterSummary(
                Dataset().load(image['meta']['datasetId'], force=True, exc=True),
                user),
            'meta': {
                'acquisition': image['meta']['acquisition'],
                'clinical': image['meta']['clinical'],
                'unstructured': image['meta']['unstructured'],
                'unstructuredExif': image['meta']['unstructuredExif']
            },
            'notes': {
                'reviewed': image['meta'].get('reviewed', None),
                'tags': image['meta']['tags']
            }
        }
        if User().canReviewDataset(user):
            output['meta']['private'] = image['privateMeta']

        return output

    def filterSummary(self, image, user=None):
        return {
            '_id': image['_id'],
            'name': image['name'],
            'updated': image['updated'],
        }

    def load(self, id, level=AccessType.ADMIN, user=None, objectId=True, force=False, fields=None,
             exc=False):
        # Avoid circular import
        from .study import Study

        # Allow annotators assigned to an image to always have read access to that image.

        # TODO: Ideally, this might set Image().resourceColl to Dataset, then add the special case
        # checks in Dataset().hasAccess. However, since AccessControlMixin.resourceColl doesn't work
        # properly (yet) with plugin types, and since we really only care about the cases where an
        # image is loaded directly (rather than when all images or datasets are iterated over);
        # adding the special case logic here works fine for now.

        try:
            return super(Image, self).load(
                id, level=level, user=user, objectId=objectId, force=force, fields=fields, exc=exc)
        except AccessException:
            image = self.load(id, objectId=objectId, force=True, fields=fields, exc=exc)
            if Study().childAnnotations(annotatorUser=user, image=image).count():
                return image
            else:
                raise

    def getHistograms(self, filterQuery, user):
        # Define facets
        categorialFacets = [
            'meta.datasetId',
            'meta.clinical.benign_malignant',
            'meta.clinical.sex',
            'meta.clinical.diagnosis_confirm_type',
            'meta.clinical.diagnosis',
            'meta.clinical.nevus_type',
            'meta.clinical.melanocytic',
            'meta.clinical.personal_hx_mm',
            'meta.clinical.family_hx_mm',
            'meta.clinical.mel_class',
            'meta.clinical.mel_type',
            'meta.clinical.mel_mitotic_index',
            'meta.clinical.mel_ulcer',
            'meta.clinical.anatom_site_general',
            'meta.acquisition.image_type',
            'meta.acquisition.dermoscopic_type'
        ]
        tagFacets = [
            'meta.tags'
        ]
        ordinalFacets = [
            (
                'meta.clinical.age_approx',
                [0, 10, 20, 30, 40, 50, 60, 70, 80, 90]
            ),
            (
                'meta.clinical.clin_size_long_diam_mm',
                # [0.0, 2.0, 4.0, 6.0, 8.0, 10.0, 12.0, 14.0,
                #  16.0, 18.0, 20.0, 100.0, 200.0, 1000.0])
                [0.0, 10.0, 20.0, 30.0, 40.0, 50.0, 60.0,
                 70.0, 80.0, 90.0, 100.0, 110.0]
            ),
            (
                'meta.clinical.mel_thick_mm',
                [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0]
            )
        ]

        # Build and run the pipeline
        folderQuery = {
            'folderId': {'$in': [
                dataset['folderId'] for dataset in Dataset().list(user=user)]}
        }
        if filterQuery:
            query = {
                '$and': [
                    folderQuery,
                    filterQuery
                ]
            }
        else:
            query = folderQuery
        facetStages = {
            '__passedFilters__': [
                {'$count': 'count'}],
        }
        for facetName in categorialFacets:
            facetId = facetName.replace('.', '__')
            facetStages[facetId] = [
                {'$sortByCount': '$' + facetName}
            ]
        for facetName in tagFacets:
            facetId = facetName.replace('.', '__')
            facetStages[facetId] = [
                {'$unwind': {
                    'path': '$' + facetName,
                    'preserveNullAndEmptyArrays': True
                }},
                {'$sortByCount': '$' + facetName}
            ]
        for facetName, boundaries in ordinalFacets:
            facetId = facetName.replace('.', '__')
            facetStages[facetId] = [
                {'$bucket': {
                    'groupBy': '$' + facetName,
                    'boundaries': boundaries,
                    'default': None
                }}
            ]
        histogram = next(iter(self.collection.aggregate([
            {'$match': query},
            {'$facet': facetStages}
        ])))

        # Fix up the pipeline result
        if not histogram['__passedFilters__']:
            # If the set of filtered images is empty, add a count manually
            histogram['__passedFilters__'] = [{'count': 0}]
        histogram['__passedFilters__'][0]['label'] = 'count'
        for facetName in itertools.chain(
                categorialFacets,
                tagFacets,
                [facetName for facetName, boundaries in ordinalFacets]
        ):
            facetId = facetName.replace('.', '__')
            histogram[facetName] = histogram.pop(facetId, [])
            histogram[facetName].sort(
                # Sort facet bins, placing "None" at the end
                key=lambda facetBin: (facetBin['_id'] is None, facetBin['_id']))
        for facetName in itertools.chain(categorialFacets, tagFacets):
            for facetBin in histogram[facetName]:
                facetBin['label'] = facetBin.pop('_id')
        for facetName, boundaries in ordinalFacets:
            boundariesMap = {
                lowBound: {
                    'label': '[%s - %s)' % (lowBound, highBound),
                    'lowBound': lowBound,
                    'highBound': highBound,
                }
                for lowBound, highBound in zip(boundaries, boundaries[1:])
            }
            for facetBin in histogram[facetName]:
                # Remove the '_id' field and replace it with the 3 other fields
                binId = facetBin.pop('_id')
                if binId is not None:
                    facetBin.update(boundariesMap[binId])
                else:
                    facetBin['label'] = None

        return histogram

    def remove(self, image, **kwargs):
        # Avoid circular import
        from .segmentation import Segmentation
        from .annotation import Annotation

        for annotation in Annotation().find({'imageId': image['_id']}):
            Annotation().remove(annotation)

        for segmentation in Segmentation().find({'imageId': image['_id']}):
            Segmentation().remove(segmentation)

        return super(Image, self).remove(image)

    def validate(self, doc):
        # TODO: implement
        return super(Image, self).validate(doc)

    def applyMetadata(self, image, metadata, save):
        """
        Apply metadata to an image.

        :param image: Image document.
        :param metadata: Image metadata.
        :param save: Whether to save the metadata to the image if validation succeeds.
        :return: Tuple of:
            - List of strings describing validation errors.
            - List of strings describing metadata warnings.
        :rtype: tuple(list, list)
        """
        errors, warnings = addImageMetadata(image, metadata)

        if not errors and save:
            self.save(image)

        return errors, warnings
