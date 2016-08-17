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
from girder.models.model_base import Model, GirderException, ValidationException

from .segmentation_helpers import ScikitSegmentationHelper


class Segmentation(Model):
    class Skill(object):
        NOVICE = 'novice'
        EXPERT = 'expert'

    def initialize(self):
        self.name = 'segmentation'
        self.ensureIndices(['imageId', 'created'])

        self.exposeFields(AccessType.READ, [
            'imageId',
            'skill',
            'creatorId',
            'startTime'
            'stopTime'
            'created'
        ])
        self.summaryFields = ['_id', 'imageId', 'skill']
        events.bind('model.item.remove_with_kwargs',
                    'isic_archive.gc_segmentation',
                    self._onDeleteItem)

    def getUserSkill(self, user):
        expertGroup = self.model('group').findOne({
            'name': 'Segmentation Experts'})
        if expertGroup['_id'] in user['groups']:
            return self.Skill.EXPERT
        noviceGroup = self.model('group').findOne({
            'name': 'Segmentation Novices'})
        if noviceGroup['_id'] in user['groups']:
            return self.Skill.NOVICE
        return None

    def createSegmentation(self, image, skill, creator, lesionBoundary):
        now = datetime.datetime.utcnow()

        segmentation = self.save({
            'imageId': image['_id'],
            'skill': skill,
            'creatorId': creator['_id'],
            'lesionBoundary': lesionBoundary,
            'created': now
        })

        # TODO: run this asynchronously
        superpixels = self.generateSuperpixels(segmentation, image)
        self.saveSuperpixels(segmentation, superpixels, 2.0)

        return segmentation

    def boundaryThumbnail(self, segmentation, image=None, width=256):
        Image = self.model('image', 'isic_archive')
        if not image:
            image = Image.load(segmentation['imageId'], force=True, exc=True)

        pilImageData = PIL_Image.fromarray(Image.imageData(image))
        pilDraw = PIL_ImageDraw.Draw(pilImageData)
        pilDraw.line(
            list(six.moves.map(tuple,
                               segmentation['lesionBoundary']
                                           ['geometry']['coordinates'][0])),
            fill=(0, 255, 0),  # TODO: make color an option
            width=5
        )

        return ScikitSegmentationHelper.writeImage(
            numpy.asarray(pilImageData), 'jpeg', width)

    def generateSuperpixels(self, segmentation, image=None):
        Image = self.model('image', 'isic_archive')
        if not image:
            image = Image.load(segmentation['imageId'], force=True, exc=True)

        imageData = Image.imageData(image)
        # coords = segmentation['lesionBoundary']['geometry']['coordinates'][0]

        superpixels = ScikitSegmentationHelper.superpixels(imageData)
        return superpixels

    def saveSuperpixels(self, segmentation, superpixels, version):
        """
        :type segmentation: dict
        :type superpixels: file-like object or numpy.ndarray
        :type version: float
        :return: The Girder File containing the PNG-encoded superpixel labels.
        :rtype: dict
        """
        if isinstance(superpixels, numpy.ndarray):
            superpixels = ScikitSegmentationHelper.writeImage(
                superpixels, 'png')

        self.removeSuperpixels(segmentation)

        superpixelsFile = self.model('upload').uploadFromFile(
            obj=superpixels,
            size=len(superpixels.getvalue()),
            name='%s_superpixels.png' % segmentation['_id'],
            user={'_id': segmentation['creatorId']},
            mimeType='image/png'
        )
        # Uploads re-lookup the passed "parent" item, so it can't be set in
        #  uploadFromFile
        superpixelsFile['itemId'] = segmentation['_id']
        superpixelsFile['superpixelVersion'] = version
        superpixelsFile = self.model('file').save(superpixelsFile)
        return superpixelsFile

    def removeSuperpixels(self, segmentation, **kwargs):
        superpixelsFile = self.superpixelsFile(segmentation)
        if superpixelsFile:
            fileKwargs = kwargs.copy()
            fileKwargs.pop('updateItemSize', None)
            # If the file has an itemId, Girder will attempt to update folder
            #   sizes (which don't exist)
            superpixelsFile['itemId'] = None
            self.model('file').remove(superpixelsFile, updateItemSize=False,
                                      **fileKwargs)

    def superpixelsFile(self, segmentation, version=None):
        """
        :type segmentation: dict
        :type version: float or None
        :rtype: dict or None
        """
        query = {'itemId': segmentation['_id']}
        if version is not None:
            query['superpixelVersion'] = version
        return self.model('file').findOne(query)

    def superpixelsData(self, segmentation, version=None):
        """
        :type segmentation: dict
        :type version: float or None
        :rtype: numpy.ndarray
        """
        superpixelsFile = self.superpixelsFile(segmentation, version)
        if not superpixelsFile:
            raise GirderException('No superpixels file in segmentation.')

        # TODO: reduce duplication with Image.imageData
        superpixelsFileStream = six.BytesIO()
        superpixelsFileStream.writelines(
            self.model('file').download(superpixelsFile, headers=False)()
        )

        # Scikit-Image is ~70ms faster at loading images
        superpixels = ScikitSegmentationHelper.loadImage(superpixelsFileStream)
        return superpixels

    def _onDeleteItem(self, event):
        item = event.info['document']
        # TODO: can we tell if this item is an image?
        for segmentation in self.find({
            'imageId': item['_id']
        }):
            self.remove(segmentation, **event.info['kwargs'])

    def remove(self, segmentation, **kwargs):
        self.removeSuperpixels(segmentation, **kwargs)
        super(Segmentation, self).remove(segmentation)

    def validate(self, doc):
        try:
            assert set(six.viewkeys(doc)) == {
                'imageId', 'skill', 'creatorId', 'lesionBoundary', 'created'}

            assert isinstance(doc['imageId'], ObjectId)
            assert self.model('image', 'isic_archive').find(
                {'_id': doc['imageId']}).count()

            assert doc['skill'] in {self.Skill.NOVICE, self.Skill.EXPERT}

            assert isinstance(doc['creatorId'], ObjectId)
            assert self.model('user').find(
                {'_id': doc['creatorId']}).count()

            assert isinstance(doc['lesionBoundary'], dict)
            assert set(six.viewkeys(doc['lesionBoundary'])) == {
                'type', 'properties', 'geometry'}

            assert doc['lesionBoundary']['type'] == 'Feature'

            assert isinstance(doc['lesionBoundary']['properties'], dict)
            assert set(six.viewkeys(doc['lesionBoundary']['properties'])) <= {
                'source', 'startTime', 'stopTime', 'seedPoint', 'tolerance'}
            assert set(six.viewkeys(doc['lesionBoundary']['properties'])) >= {
                'source', 'startTime', 'stopTime'}
            assert doc['lesionBoundary']['properties']['source'] in {
                'autofill', 'manual pointlist'}
            assert isinstance(doc['lesionBoundary']['properties']['startTime'],
                              datetime.datetime)
            assert isinstance(doc['lesionBoundary']['properties']['stopTime'],
                              datetime.datetime)

            assert isinstance(doc['lesionBoundary']['geometry'], dict)
            assert set(six.viewkeys(doc['lesionBoundary']['geometry'])) == {
                'type', 'coordinates'}
            assert doc['lesionBoundary']['geometry']['type'] == 'Polygon'
            assert isinstance(doc['lesionBoundary']['geometry']['coordinates'],
                              list)
            assert len(doc['lesionBoundary']['geometry']['coordinates']) == 1
            assert isinstance(
                doc['lesionBoundary']['geometry']['coordinates'][0], list)
            assert len(doc['lesionBoundary']['geometry']['coordinates'][0]) > 2
            assert doc['lesionBoundary']['geometry']['coordinates'][0][0] == \
                doc['lesionBoundary']['geometry']['coordinates'][0][-1]
            for coord in doc['lesionBoundary']['geometry']['coordinates'][0]:
                assert isinstance(coord, list)
                assert len(coord) == 2
                for val in coord:
                    assert isinstance(val, (int, float))
                    assert val >= 0

            assert isinstance(doc['created'], datetime.datetime)

        except (AssertionError, KeyError):
            # TODO: message
            raise ValidationException('')
        return doc
