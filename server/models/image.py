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
import six

from girder.constants import AccessType
from girder.models.model_base import AccessException
from girder.models.item import Item as ItemModel
from girder.utility import assetstore_utilities

from .. import constants
from ..provision_utility import getAdminUser
from .segmentation_helpers import ScikitSegmentationHelper
from ..upload import TempDir


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
            'clinical': {},
            'acquisition': {},
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

        # this adds image['largeImage']['originalId'] and allows the subsequent
        # use of Image.originalFile and Image.imageData
        image = self._generateLargeimage(image, originalFile)

        image = self._generateSuperpixels(image)

        # TODO: copy license from dataset to image

        imageData = self.imageData(image)
        image['meta']['acquisition']['pixelsY'] = imageData.shape[0]
        image['meta']['acquisition']['pixelsX'] = imageData.shape[1]
        image = self.save(image)

        return image

    def _generateLargeimage(self, image, originalFile):
        # TODO: replace this with usage of large_image
        assetstore = self.model('assetstore').getCurrent()
        assetstoreAdapter = assetstore_utilities.getAssetstoreAdapter(
            assetstore)

        with TempDir() as tempDir:
            largeimageFileName = '%s.tiff' % image['name']
            largeimageFilePath = os.path.join(tempDir, largeimageFileName)

            originalFilePath = assetstoreAdapter.fullPath(originalFile)

            convert_command = (
                '/usr/local/bin/vips',
                'tiffsave',
                '\'%s\'' % originalFilePath,
                '\'%s\'' % largeimageFilePath,
                '--compression', 'jpeg',
                '--Q', '90',
                '--tile',
                '--tile-width', '256',
                '--tile-height', '256',
                '--pyramid',
                '--bigtiff',
            )
            os.popen(' '.join(convert_command))

            # upload converted image
            with open(largeimageFilePath, 'rb') as largeimageFileStream:
                largeImageFile = self.model('upload').uploadFromFile(
                    obj=largeimageFileStream,
                    size=os.path.getsize(largeimageFilePath),
                    name=largeimageFileName,
                    parentType='item',
                    parent=image,
                    user={'_id': image['creatorId']},
                    mimeType='image/tiff',
                )
            os.remove(largeimageFilePath)
            # reload image, since its 'size' has changed in the database
            image = self.load(image['_id'], force=True, exc=True)

            image['largeImage'] = {
                'fileId': largeImageFile['_id'],
                'sourceName': 'tiff',
                'originalId': originalFile['_id']
            }
            image = self.save(image)

            return image

    def _generateSuperpixels(self, image):
        # TODO: run this asynchronously (self.imageData can't be used)
        SUPERPIXEL_VERSION = 3.0

        imageData = self.imageData(image)

        superpixelsData = ScikitSegmentationHelper.superpixels(imageData)
        superpixelsEncodedStream = ScikitSegmentationHelper.writeImage(
            superpixelsData, 'png')

        superpixelsFile = self.model('upload').uploadFromFile(
            obj=superpixelsEncodedStream,
            size=len(superpixelsEncodedStream.getvalue()),
            name='%s_superpixels_v%s.png' % (image['name'], SUPERPIXEL_VERSION),
            parentType='item',
            parent=image,
            user={'_id': image['creatorId']},
            mimeType='image/png'
        )
        superpixelsFile['superpixelVersion'] = SUPERPIXEL_VERSION
        superpixelsFile = self.model('file').save(superpixelsFile)

        image['superpixelsId'] = superpixelsFile['_id']
        image = self.save(image)
        return image

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
        if not any(
            self.model('group').findOne(
                {'name': groupName}
            )['_id'] in user.get('groups', [])
            for groupName in
            ['Phase 0', 'Segmentation Novices', 'Segmentation Experts']
        ):
            # Check if all images are part of annotation studies that this user
            #   is part of
            imageIds = list(set(image['_id'] for image in images))
            annotations = self.model('annotation', 'isic_archive').find({
                'imageId': {'$in': imageIds},
                'userId': user['_id']
            })
            if len(imageIds) != len(annotations):
                raise AccessException(
                    'User does not have permission to flag these images.')

        phase0Folders = [
            self.model('folder').load(phase0Folder, force=True, exc=True)
            for phase0Folder in
            set(image['folderId'] for image in images)
        ]

        flaggedCollection = self.model('collection').findOne(
            {'name': 'Flagged Images'})

        datasetFlaggedFolders = {
            phase0Folder['_id']: self.model('folder').createFolder(
                parent=flaggedCollection,
                name=phase0Folder['name'],
                description='',
                parentType='collection',
                public=None,
                creator=getAdminUser(),
                allowRename=False,
                reuseExisting=True
            )
            for phase0Folder in phase0Folders
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
