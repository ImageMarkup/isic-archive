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

import datetime
import mimetypes
import os
import re
import six

from girder import events
from girder.constants import AccessType, TokenScope
from girder.models.model_base import AccessException
from girder.models.item import Item as ItemModel
from girder.plugins.worker import utils as workerUtils

from . import segmentation_helpers
from .. import constants
from ..provision_utility import getAdminUser
from .segmentation_helpers import ScikitSegmentationHelper


class Image(ItemModel):
    def initialize(self):
        super(Image, self).initialize()

        self._filterKeys[AccessType.READ].clear()
        self.exposeFields(level=AccessType.READ, fields=[
            '_id', 'name', 'description', 'meta', 'created', 'creatorId',
            'updated', 'folderId'
            # TODO: re-add once converted file no longer contributes to size
            # 'size',
        ])
        self.summaryFields = ['_id', 'name', 'updated']
        self.prefixSearchFields = ['lowerName', 'name']

        events.bind('data.process',
                    'onSuperpixelsUpload', self.onSuperpixelsUpload)

    def createImage(self, imageDataStream, imageDataSize, originalName,
                    dataset, creator):
        newIsicId = self.model('setting').get(
            constants.PluginSettings.MAX_ISIC_ID, default=-1) + 1
        image = self.createItem(
            name='ISIC_%07d' % newIsicId,
            creator=creator,
            folder=dataset,
            description=''
        )
        self.model('setting').set(
            constants.PluginSettings.MAX_ISIC_ID, newIsicId)

        image = self.setMetadata(image, {
            'acquisition': {},
            'clinical': {},
            'unstructured': {},
            'originalFilename': originalName
        })

        originalFile = self.model('upload').uploadFromFile(
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
        # the subsequent use of Image.originalFile and Image.imageData
        self._generateLargeimage(image, originalFile)

        self._generateSuperpixels(image)

        # TODO: copy license from dataset to image

        imageData = self.imageData(image)
        image['meta']['acquisition']['pixelsY'] = imageData.shape[0]
        image['meta']['acquisition']['pixelsX'] = imageData.shape[1]
        image = self.save(image)

        return image

    def _generateLargeimage(self, image, originalFile):
        ImageItem = self.model('image_item', 'large_image')
        Token = self.model('token')
        User = self.model('user', 'isic_archive')

        user = User.load(image['creatorId'], force=True, exc=True)
        token = Token.createToken(
            user=user,
            days=0.25,  # 6 hours
            scope=[TokenScope.DATA_READ, TokenScope.DATA_WRITE])

        job = ImageItem.createImageItem(image, originalFile, user, token)
        return job

    def _generateSuperpixels(self, image):
        Job = self.model('job', 'jobs')
        Token = self.model('token')
        User = self.model('user', 'isic_archive')

        SUPERPIXEL_VERSION = 3.0

        user = User.load(image['creatorId'], force=True, exc=True)
        token = Token.createToken(
            user=user,
            days=0.25,  # 6 hours
            scope=[TokenScope.DATA_READ, TokenScope.DATA_WRITE])

        with open(os.path.join(
                os.path.dirname(__file__),
                '_generate_superpixels.py'), 'r') as scriptStream:
            script = scriptStream.read()

        title = 'superpixels v%s generation: %s' % (
            SUPERPIXEL_VERSION, image['name'])
        job = Job.createJob(
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
            Job.createJobToken(job),
            logPrint=True
        )
        job['meta'] = {
            'creator': 'isic_archive',
            'task': 'generateSuperpixels',
            'imageId': image['_id'],
            'imageName': image['name'],
            'superpixelsVersion': SUPERPIXEL_VERSION
        }
        job = Job.save(job)

        Job.scheduleJob(job)
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
            '^%s_superpixels_v([0-9.]+)\.png' % image['name'],
            superpixelsFile['name'])
        if not superpixelsFileNameMatch:
            return

        superpixelsVersion = float(superpixelsFileNameMatch.group(1))
        superpixelsFile['superpixelVersion'] = superpixelsVersion
        superpixelsFile = self.model('file').save(superpixelsFile)

        image['superpixelsId'] = superpixelsFile['_id']
        self.save(image)

    def originalFile(self, image):
        return self.model('file').load(
            image['largeImage']['originalId'], force=True, exc=True)

    def superpixelsFile(self, image):
        return self.model('file').load(
            image['superpixelsId'], force=True, exc=True)

    def _decodeDataFromFile(self, fileObj):
        fileStream = six.BytesIO()
        fileStream.writelines(
            self.model('file').download(fileObj, headers=False)()
        )
        # Scikit-Image is ~70ms faster at decoding image data
        data = ScikitSegmentationHelper.loadImage(fileStream)
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
        imageCollection = self.model('collection').findOne({
            'name': 'Lesion Images'})

        datasetQuery = {
            'baseParentId': imageCollection['_id']
        }
        if query:
            datasetQuery.update(query)
        return datasetQuery

    def find(self, query=None, **kwargs):
        imageQuery = self._findQueryFilter(query)
        return super(Image, self).find(imageQuery, **kwargs)

    def findOne(self, query=None, **kwargs):
        if query and '_id' in query:
            # Allow loading images directly by id from other collections
            # TODO: this actually allows any item to be loaded as an image,
            # which is not intended
            # TODO: remove this, once all images are in the "Lesion Images"
            # collection
            imageQuery = query
        else:
            imageQuery = self._findQueryFilter(query)
        return super(Image, self).findOne(imageQuery, **kwargs)

    def flag(self, image, reason, user):
        self.flagMultiple([image], reason, user)

    def flagMultiple(self, images, reason, user):
        # TODO: change to use direct permissions on the images
        if (not user['admin']) and (not any(
            self.model('group').findOne(
                {'name': groupName}
            )['_id'] in user.get('groups', [])
            for groupName in
            ['Dataset QC Reviewers', 'Segmentation Novices',
             'Segmentation Experts']
        )):
            # Check if all images are part of annotation studies that this user
            #   is part of
            imageIds = list(set(image['_id'] for image in images))
            annotations = self.model('annotation', 'isic_archive').find({
                'imageId': {'$in': imageIds},
                'userId': user['_id']
            })
            if len(imageIds) != annotations.count():
                raise AccessException(
                    'User does not have permission to flag these images.')

        prereviewFolders = [
            self.model('folder').load(prereviewFolder, force=True, exc=True)
            for prereviewFolder in
            set(image['folderId'] for image in images)
        ]

        flaggedCollection = self.model('collection').findOne(
            {'name': 'Flagged Images'})

        datasetFlaggedFolders = {
            prereviewFolder['_id']: self.model('folder').createFolder(
                parent=flaggedCollection,
                name=prereviewFolder['name'],
                description='',
                parentType='collection',
                public=None,
                creator=getAdminUser(),
                allowRename=False,
                reuseExisting=True
            )
            for prereviewFolder in prereviewFolders
        }

        flagMetadata = {
            'flaggedUserId': user['_id'],
            'flaggedTime': datetime.datetime.utcnow(),
            'flaggedReason': reason,
        }
        for image in images:
            self.model('item').setMetadata(image, flagMetadata)
            # TODO: deal with any existing studies with this image
            self.model('item').move(image,
                                    datasetFlaggedFolders[image['folderId']])

    def validate(self, doc):
        # TODO: implement
        return super(Image, self).validate(doc)
