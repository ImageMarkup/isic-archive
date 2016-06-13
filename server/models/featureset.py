#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime

from girder.constants import AccessType
from girder.models.model_base import Model


class Featureset(Model):

    def initialize(self):
        self.name = 'featureset'
        self.exposeFields(AccessType.READ, (
            '_id',
            'name',
            'creatorId',
            'created',
            'version',
            'image_features',
            'region_features'
        ))
        self.summaryFields = ('_id', 'name', 'version')


    def createFeatureset(self, name, version, creator):
        now = datetime.datetime.utcnow()

        return self.save({
            'name': name,
            'creatorId': creator['_id'],
            'created': now,
            'version': version,
            'image_features': [],
            'region_features': [],
        })


    def validate(self, doc):
        # raise ValidationException
        return doc
