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

from girder.constants import AccessType
from girder.models.model_base import Model


class Featureset(Model):
    def initialize(self):
        self.name = 'featureset'
        self.exposeFields(AccessType.READ, [
            '_id',
            'name',
            'creatorId',
            'created',
            'version',
            'globalFeatures',
            'localFeatures'
        ])
        self.summaryFields = ['_id', 'name', 'version']
        self.prefixSearchFields = [('name', 'i')]

    def createFeatureset(self, name, version, creator,
                         globalFeatures, localFeatures):
        now = datetime.datetime.utcnow()
        return self.save({
            'name': name,
            'creatorId': creator['_id'],
            'created': now,
            'version': version,
            'globalFeatures': globalFeatures,
            'localFeatures': localFeatures,
        })

    def validate(self, doc):
        # TODO: implement
        return doc
