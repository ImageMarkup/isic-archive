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
import re

import six

from girder.constants import AccessType
from girder.models.model_base import Model, ValidationException


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

    def _validateFeatureId(self, name):
        if not isinstance(name, six.string_types):
            raise ValidationException('ID must be a string')
        if not name:
            raise ValidationException('ID must not be empty')
        if not re.match('^[a-z0-9-_/]+$', name):
            raise ValidationException(
                'ID may only contain lower-case letters, numbers, '
                'dashes, underscores, and forward-slashes')

    def validate(self, doc):  # noqa - C901
        User = self.model('user', 'isic_archive')

        extraFields = set(six.viewkeys(doc)) - {
            '_id', 'name', 'creatorId', 'created', 'version',
            'globalFeatures', 'localFeatures'}
        if extraFields:
            raise ValidationException('Featureset has extra fields: %s.' %
                                      ', '.join(sorted(extraFields)))

        if not (doc.get('name') and isinstance(doc['name'], six.string_types)):
            raise ValidationException(
                'Featureset field "name" must be a non-empty string.')

        # This is slower, but we don't save featuresets very often
        if not User.load(doc.get('creatorId'), force=True, exc=False,
                         fields=['_id']):
            raise ValidationException(
                'Featureset field "creatorId" must reference a user.')

        if not isinstance(doc.get('created'), datetime.datetime):
            raise ValidationException(
                'Featureset field "created" must be a datetime.')

        if not isinstance(doc.get('version'), float):
            raise ValidationException(
                'Featureset field "version" must be a float.')

        duplicateQuery = {
            'name': doc['name'],
            'version': doc['version']
        }
        if '_id' in doc:
            duplicateQuery['_id'] = {'$ne': doc['_id']}
        if self.findOne(duplicateQuery, fields=['_id']):
            raise ValidationException(
                'A Featureset with this name and version already exists.')

        for featureType in ['globalFeatures', 'localFeatures']:
            if not isinstance(doc.get(featureType), list):
                raise ValidationException(
                    'Featureset field "%s" must be a list.' % featureType)
            for feature in doc[featureType]:
                if not isinstance(feature, dict):
                    raise ValidationException(
                        'Featureset field "%s" must contain dicts.' %
                        featureType)

                try:
                    self._validateFeatureId(feature.get('id'))
                except ValidationException as e:
                    raise ValidationException(
                        'Featureset sub-fields "%s.id" is invalid: %s.' %
                        (featureType, str(e)))

                if not isinstance(feature.get('name'), list):
                    raise ValidationException(
                        'Featureset sub-fields "%s.name" must be lists.' %
                        featureType)
                if not all(
                        featureNameComponent and
                        isinstance(featureNameComponent, six.string_types)
                        for featureNameComponent in feature['name']):
                    raise ValidationException(
                        'Featureset sub-fields "%s.name" must be lists of '
                        'non-empty strings.' % featureType)

                allowedFields = {'id', 'name', 'type'}
                if featureType == 'globalFeatures':
                    if feature.get('type') != 'radio':
                        raise ValidationException(
                            'Featureset sub-fields "globalFeatures.type" must '
                            'equal "radio".')
                    allowedFields.add('options')
                    if not isinstance(feature.get('options'), list):
                        raise ValidationException(
                            'Featureset sub-fields "globalFeatures.options" '
                            'must be lists.')
                    for option in feature['options']:
                        if not isinstance(option, dict):
                            raise ValidationException(
                                'Featureset sub-fields "globalFeatures.options"'
                                ' must be lists of dicts.')
                        if not set(six.viewkeys(option)) == {'id', 'name'}:
                            raise ValidationException(
                                'Featureset sub-fields "globalFeatures.options"'
                                ' must be lists of dicts with "id" and "name".')

                        try:
                            self._validateFeatureId(option['id'])
                        except ValidationException as e:
                            raise ValidationException(
                                'Featureset sub-field '
                                '"globalFeatures.options.id" is invalid: %s.' %
                                str(e))

                        if not (option['name'] and
                                isinstance(option['name'], six.string_types)):
                            raise ValidationException(
                                'Featureset sub-fields '
                                '"globalFeatures.options.name" must be '
                                'non-empty strings.')

                else:  # featureType == 'localFeatures':
                    if feature.get('type') != 'superpixel':
                        raise ValidationException(
                            'Featureset sub-fields "globalFeatures.type" must '
                            'equal "superpixel".')

                extraFields = set(six.viewkeys(feature)) - allowedFields
                if extraFields:
                    raise ValidationException(
                        'Featureset sub-field "%s" has extra fields: %s.' %
                        (featureType, ', '.join(sorted(extraFields))))

        return doc
