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
import six

import geojson

from girder.constants import AccessType
from girder.models.model_base import AccessException, GirderException
from girder.models.item import Item as ItemModel

from .. import constants
from ..provision_utility import _ISICCollection
from .segmentation_helpers import ScikitSegmentationHelper, \
    OpenCVSegmentationHelper


class Image(ItemModel):
    def initialize(self):
        super(Image, self).initialize()

        self._filterKeys[AccessType.READ].clear()
        self.exposeFields(level=AccessType.READ, fields=[
            '_id', 'name', 'description', 'meta', 'created', 'creatorId',
            'updated',
            # TODO: re-add once converted file no longer contributes to size
            # 'size',
        ])
        self.summaryFields = ['_id', 'name', 'updated']
        self.prefixSearchFields = ['lowerName', 'name']

    def createImage(self, creator, parentFolder):
        newIsicId = self.model('setting').get(
            constants.PluginSettings.MAX_ISIC_ID, default=-1) + 1

        image = self.createItem(
            name='ISIC_%07d' % newIsicId,
            creator=creator,
            folder=parentFolder,
            description=''
        )
        self.setMetadata(image, {
            'clinical': {},
            'acquisition': {}
        })

        self.model('setting').set(
            constants.PluginSettings.MAX_ISIC_ID, newIsicId)

        return image

    def originalFile(self, image):
        return self.model('file').findOne({
            'itemId': image['_id'],
            # TODO: make this more robust (original image may not be a JPEG)
            'name': {'$in': [
                '%s.jpg' % image['name'],
                '%s.png' % image['name']
            ]}
        })

    def imageData(self, image):
        """
        Return the RGB image data associated with this image.

        :rtype: numpy.ndarray
        """
        imageFile = self.originalFile(image)

        imageFileStream = six.BytesIO()
        imageFileStream.writelines(
            self.model('file').download(imageFile, headers=False)()
        )

        # Scikit-Image is ~70ms faster at loading images
        imageData = ScikitSegmentationHelper.loadImage(imageFileStream)
        return imageData

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
            ['Phase 0', 'Phase 1a', 'Phase 1b']
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
            phase0Folder['_id']: _ISICCollection.createFolder(
                name=phase0Folder['name'],
                description='',
                parent=flaggedCollection,
                parent_type='collection'
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

    def doSegmentation(self, image, seedCoord, tolerance):
        """
        Run a lesion segmentation.

        :param image: A Girder Image item.
        :param seedCoord: X, Y coordinates of the segmentation seed point.
        :type seedCoord: tuple[int]
        :param tolerance: The intensity tolerance value for the segmentation.
        :type tolerance: int
        :return: The lesion segmentation, as a GeoJSON Polygon Feature.
        :rtype: geojson.Feature
        """
        imageData = self.imageData(image)

        if not(
            # The imageData has a shape of (rows, cols), the seed is (x, y)
            0.0 <= seedCoord[0] <= imageData.shape[1] and
            0.0 <= seedCoord[1] <= imageData.shape[0]
        ):
            raise GirderException('seedCoord is out of bounds')

        # OpenCV is significantly faster at segmentation right now
        contourCoords = OpenCVSegmentationHelper.segment(
            imageData, seedCoord, tolerance)

        contourFeature = geojson.Feature(
            geometry=geojson.Polygon(
                coordinates=(contourCoords.tolist(),)
            ),
            properties={
                'source': 'autofill',
                'seedPoint': seedCoord,
                'tolerance': tolerance
            }
        )
        return contourFeature

    def validate(self, doc):
        # TODO: implement
        return super(Image, self).validate(doc)
