#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
import six

from bson import ObjectId
from enum import Enum
import numpy

from girder import events
from girder.constants import AccessType
from girder.models.model_base import Model, ValidationException

from .segmentation_helpers import ScikitSegmentationHelper


class Segmentation(Model):

    class Skill(Enum):
        NOVICE = 'novice'
        EXPERT = 'expert'


    def initialize(self):
        self.name = 'segmentation'
        self.ensureIndices(['imageId', 'created'])

        self.exposeFields(AccessType.READ, (
            'imageId',
            'skill',
            'creatorId',
            'startTime'
            'stopTime'
            'created'
        ))
        events.bind('model.item.remove_with_kwargs',
                    'isic_archive.gc_segmentation',
                    self._onDeleteItem)


    def createSegmentation(self, image, skill, creator):
        if not isinstance(skill, self.Skill):
            raise TypeError('skill must be an instance of Skill')

        now = datetime.datetime.utcnow()

        return self.save({
            'imageId': image['_id'],
            'skill': skill.value,
            'creatorId': creator['_id'],

            'lesionBoundary': {
                'type': 'Feature',
                'properties': {
                    'source': None,
                    'startTime': None,
                    'stopTime': None,
                },
                'geometry': {
                    'type': 'Polygon',
                    'coordinates': []
                },
            },
            'superpixels': None,

            'created': now
        })


    def generateSuperpixels(self, segmentation, image=None):
        Image = self.model('image', 'isic_archive')
        if not image:
            image = Image.load(segmentation['imageId'], force=True, exc=True)

        image_data = Image.imageData(image)
        coords = segmentation['lesionBoundary']['geometry']['coordinates'][0]

        superpixels = ScikitSegmentationHelper.superpixels(image_data, coords)

        return superpixels


    def saveSuperpixels(self, segmentation, superpixels):
        """
        :type segmentation: dict
        :type superpixels: file-like object or numpy.ndarray
        :return: The Girder File containing the PNG-encoded superpixel labels.
        :rtype: dict
        """
        if isinstance(superpixels, numpy.ndarray):
            superpixels = ScikitSegmentationHelper.writeImage(
                superpixels, 'png')

        self.removeSuperpixels(segmentation)

        return self.model('upload').uploadFromFile(
            obj=superpixels,
            size=len(superpixels.getvalue()),
            name='%s_superpixels.png' % segmentation['_id'],
            parentType='item',
            parent=segmentation,
            user={'_id': segmentation['creatorId']},
            mimeType='image/png'
        )


    def removeSuperpixels(self, segmentation, **kwargs):
        superpixels_file = self.superpixelsFile(segmentation)
        if superpixels_file:
            fileKwargs = kwargs.copy()
            fileKwargs.pop('updateItemSize', None)
            self.model('file').remove(superpixels_file, updateItemSize=False,
                                      **fileKwargs)


    def superpixelsFile(self, segmentation):
        """
        :type segmentation: dict
        :rtype: models.file.File or None
        """
        return self.model('file').findOne({'itemId': segmentation['_id']})


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

            # TODO: better use of Enum
            assert doc['skill'] in {'novice', 'expert'}

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
                assert isinstance(coord[0], (int, float))
                assert isinstance(coord[1], (int, float))

            assert isinstance(doc['created'], datetime.datetime)

        except AssertionError:
            # TODO: message
            raise ValidationException('')
        return doc
