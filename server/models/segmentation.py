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

from bson import ObjectId
import numpy
from PIL import Image as PIL_Image, ImageDraw as PIL_ImageDraw

from girder import events
from girder.constants import AccessType
from girder.models.file import File
from girder.models.model_base import Model, GirderException, ValidationException
from girder.models.upload import Upload

from .image import Image
from .segmentation_helpers import ScikitSegmentationHelper, OpenCVSegmentationHelper
from .user import User


class Segmentation(Model):
    class Skill(object):
        NOVICE = 'novice'
        EXPERT = 'expert'

    def initialize(self):
        self.name = 'segmentation'
        self.ensureIndices(['imageId', 'created'])

        self.exposeFields(AccessType.READ, [
            'imageId',
            'creatorId',
            'created',
            'reviews',
            'meta'
        ])
        self.summaryFields = ['_id', 'created']
        events.bind('model.item.remove_with_kwargs',
                    'isic_archive.gc_segmentation',
                    self._onDeleteItem)

    def doSegmentation(self, image, seedCoord, tolerance):
        """
        Run a lesion segmentation.

        :param image: A Girder Image item.
        :param seedCoord: (X, Y) coordinates of the segmentation seed point.
        :type seedCoord: tuple[int]
        :param tolerance: The intensity tolerance value for the segmentation.
        :type tolerance: int
        :return: The lesion segmentation, as a mask.
        :rtype: numpy.ndarray
        """
        imageData = Image().imageData(image)

        if not(
            # The imageData has a shape of (rows, cols), the seed is (x, y)
            0.0 <= seedCoord[0] <= imageData.shape[1] and
            0.0 <= seedCoord[1] <= imageData.shape[0]
        ):
            raise GirderException('seedCoord is out of bounds')

        # OpenCV is significantly faster at segmentation right now
        mask = OpenCVSegmentationHelper.segment(
            imageData, seedCoord, tolerance)

        return mask

    def doContourSegmentation(self, image, seedCoord, tolerance):
        mask = self.doSegmentation(image, seedCoord, tolerance)
        contour = OpenCVSegmentationHelper.maskToContour(
            mask,
            paddedInput=False,
            safe=False
        )
        return contour

    def createSegmentation(self, image, creator, mask, meta=None):
        now = datetime.datetime.utcnow()

        if mask is not None:
            mask = self._validateMask(mask, image)
            maskOutputStream = ScikitSegmentationHelper.writeImage(
                mask, encoding='png')

        segmentation = self.save({
            'imageId': image['_id'],
            'creatorId': creator['_id'],
            'created': now,
            'maskId': None,
            'reviews': [],
            'meta': meta or {}
        })

        if mask is not None:
            maskFile = Upload().uploadFromFile(
                obj=maskOutputStream,
                size=len(maskOutputStream.getvalue()),
                name='%s_segmentation.png' % (image['name']),
                # TODO: change this once a bug in upstream Girder is fixed
                parentType='segmentation',
                parent=segmentation,
                attachParent=True,
                user=creator,
                mimeType='image/png'
            )
            # TODO: remove this once a bug in upstream Girder is fixed
            maskFile['attachedToType'] = ['segmentation', 'isic_archive']
            maskFile = File().save(maskFile)

            segmentation['maskId'] = maskFile['_id']

        # review will save the segmentation
        segmentation = self.review(
            segmentation=segmentation,
            approved=mask is not None,
            user=creator,
            time=now)

        return segmentation

    def maskFile(self, segmentation):
        if segmentation['maskId'] is None:
            return None
        return File().load(segmentation['maskId'], force=True, exc=True)

    def maskData(self, segmentation):
        """
        Return the mask data associated with this segmentation.

        :rtype: numpy.ndarray
        """
        maskFile = self.maskFile(segmentation)
        if maskFile is None:
            return None
        return Image()._decodeDataFromFile(maskFile)

    def boundaryThumbnail(self, segmentation, image=None, width=256):
        if not image:
            image = Image().load(segmentation['imageId'], force=True, exc=True)

        mask = self.maskData(segmentation)
        if mask is None:
            return None
        contour = OpenCVSegmentationHelper.maskToContour(
            mask, paddedInput=False)

        pilImageData = PIL_Image.fromarray(Image.imageData(image))
        pilDraw = PIL_ImageDraw.Draw(pilImageData)
        pilDraw.line(
            list(six.moves.map(tuple, contour)),
            fill=(0, 255, 0),  # TODO: make color an option
            width=5
        )

        return ScikitSegmentationHelper.writeImage(
            numpy.asarray(pilImageData), 'jpeg', width)

    def review(self, segmentation, approved, user, time=None):
        skill = User().getSegmentationSkill(user)
        if time is None:
            time = datetime.datetime.utcnow()

        segmentation['reviews'].append({
            'userId': user['_id'],
            'skill': skill,
            'time': time,
            'approved': approved
        })

        return self.save(segmentation)

    def _onDeleteItem(self, event):
        item = event.info['document']
        # TODO: can we tell if this item is an image?
        for segmentation in self.find({
            'imageId': item['_id']
        }):
            self.remove(segmentation, **event.info['kwargs'])

    def remove(self, segmentation, **kwargs):
        # A segmentation could be "failed" and have a "maskId" of None
        if segmentation['maskId'] is not None:
            File().remove(self.maskFile(segmentation))
        super(Segmentation, self).remove(segmentation, **kwargs)

    def _validateMask(self, mask, image):
        if len(mask.shape) != 2:
            raise ValidationException('Mask must be a single-channel image.')
        if mask.shape != (
                image['meta']['acquisition']['pixelsY'],
                image['meta']['acquisition']['pixelsX']):
            raise ValidationException(
                'Mask must have the same dimensions as the image.')
        if mask.dtype != numpy.uint8:
            raise ValidationException('Mask may only contain 8-bit values.')

        maskValues = frozenset(numpy.unique(mask))
        if maskValues <= {0, 255}:
            # Expected values
            pass
        elif len(maskValues) == 1:
            # Single value, non-0
            mask.fill(0)
        elif len(maskValues) == 2:
            # Binary image with high value other than 255 can be corrected
            lowValue = min(maskValues)
            if lowValue != 0:
                mask[mask == lowValue] = 0
            highValue = max(maskValues)
            if highValue != 255:
                mask[mask == highValue] = 255
        else:
            raise ValidationException(
                'Mask may only contain values of 0 and 255.')

        contours = OpenCVSegmentationHelper._maskToContours(mask)
        if len(contours) > 1:
            raise ValidationException(
                'Mask may not contain multiple disconnected components.')

        return mask

    def validate(self, doc):
        try:
            assert set(six.viewkeys(doc)) >= {
                'imageId', 'creatorId', 'created', 'maskId', 'reviews', 'meta'}
            assert set(six.viewkeys(doc)) <= {
                '_id', 'imageId', 'creatorId', 'created', 'maskId', 'reviews',
                'meta'}

            assert isinstance(doc['imageId'], ObjectId)
            assert Image().find({'_id': doc['imageId']}).count()

            assert isinstance(doc['creatorId'], ObjectId)
            assert User().find({'_id': doc['creatorId']}).count()

            assert isinstance(doc['created'], datetime.datetime)

            if doc['maskId']:
                assert isinstance(doc['maskId'], ObjectId)
                assert File().find({'_id': doc['maskId']}).count()

            assert isinstance(doc['reviews'], list)
            for review in doc['reviews']:
                assert set(six.viewkeys(review)) == {
                    'userId', 'skill', 'time', 'approved'}
                assert isinstance(review['userId'], ObjectId)
                assert User().find({'_id': review['userId']}).count()
                assert review['skill'] in {self.Skill.NOVICE, self.Skill.EXPERT}
                assert isinstance(review['time'], datetime.datetime)
                assert isinstance(review['approved'], bool)

            assert isinstance(doc['meta'], dict)

        except (AssertionError, KeyError):
            # TODO: message
            raise ValidationException('')
        return doc
