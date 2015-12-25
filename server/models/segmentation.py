#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime

from enum import Enum

from girder.constants import AccessType
from girder.models.model_base import Model

from .segmentation_helpers import ScikitSegmentationHelper


class Segmentation(Model):

    class Skill(Enum):
        NOVICE = 'novice'
        EXPERT = 'expert'


    def initialize(self):
        # TODO: add indexes
        self.name = 'segmentation'
        self.exposeFields(AccessType.READ, (
            'imageId',
            'skill',
            'creatorId',
            'startTime'
            'stopTime'
            'created'
        ))


    def createSegmentation(self, image, skill, creator):
        if not isinstance(skill, self.Skill):
            raise TypeError('skill must be an instance of Skill')

        now = datetime.datetime.utcnow()

        return self.save({
            'imageId': image['_id'],
            'skill': skill,
            'creatorId': creator['_id'],

            'lesionBoundary': {
                'startTime': None,
                'stopTime': None,
                'type': 'Feature',
                'properties': {
                    'source': None
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


    def validate(self, doc):
        # raise ValidationException
        return doc
