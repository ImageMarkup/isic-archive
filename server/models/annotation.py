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

from girder.constants import AccessType
from girder.models.item import Item as ItemModel
from girder.models.model_base import ValidationException


class Annotation(ItemModel):
    def createAnnotation(self, study, segmentation, creatorUser,
                         annotatorFolder):
        image = self.model('image', 'isic_archive').load(
            segmentation['imageId'], user=creatorUser, level=AccessType.READ)

        annotationItem = self.createItem(
            folder=annotatorFolder,
            name=image['name'],
            description='',
            creator=creatorUser
        )
        # "setMetadata" will always save
        self.setMetadata(
            item=annotationItem,
            metadata={
                'studyId': study['_id'],
                'userId': annotatorFolder['meta']['userId'],
                'segmentationId': segmentation['_id'],
                'imageId': image['_id'],
                'startTime': None,
                'stopTime': None,
                'annotations': None
            }
        )
        return annotationItem

    def _findQueryFilter(self, query):
        Study = self.model('study', 'isic_archive')
        annotationQuery = {
            'baseParentId': Study.loadStudyCollection()['_id']
        }
        if query:
            annotationQuery.update(query)
        return annotationQuery

    def find(self, query=None, **kwargs):
        annotationQuery = self._findQueryFilter(query)
        return super(Annotation, self).find(annotationQuery, **kwargs)

    def findOne(self, query=None, **kwargs):
        annotationQuery = self._findQueryFilter(query)
        return super(Annotation, self).findOne(annotationQuery, **kwargs)

    def validate(self, doc):  # noqa - C901
        Study = self.model('study', 'isic_archive')
        # If annotation is fully created
        if doc.get('meta') and 'studyId' in doc['meta']:
            for field in ['studyId', 'userId', 'segmentationId', 'imageId']:
                if not isinstance(doc['meta'].get(field), ObjectId):
                    raise ValidationException(
                        'Annotation field "%s" must be an ObjectId' % field)

            study = Study.load(doc['meta']['studyId'], force=True)
            if not study:
                raise ValidationException(
                    'Annotation field "studyId" must reference an existing '
                    'Study.')

            # If annotation is complete
            if doc['meta'].get('stopTime'):
                if not isinstance(doc['meta'].get('status'), six.string_types):
                    raise ValidationException(
                        'Annotation field "status" must be a string.')
                for field in ['startTime', 'stopTime']:
                    if not isinstance(doc['meta'].get(field),
                                      datetime.datetime):
                        raise ValidationException(
                            'Annotation field "%s" must be a datetime.' % field)

                if not isinstance(doc['meta'].get('annotations'), dict):
                    raise ValidationException(
                        'Annotation field "annotations" must be a mapping '
                        '(dict).')
                featureset = Study.getFeatureset(study)
                featuresetImageFeatures = {
                    feature['id']: feature
                    for feature in
                    featureset['image_features']
                }
                featuresetRegionFeatures = {
                    feature['id']: feature
                    for feature in
                    featureset['region_features']
                }
                for featureId, featureValue in six.viewitems(
                        doc['meta']['annotations']):
                    if featureId in featuresetImageFeatures:
                        featureOptions = set(
                            option['id']
                            for option in
                            featuresetImageFeatures[featureId]['options'])
                        if featureValue not in featureOptions:
                            raise ValidationException(
                                'Annotation feature "%s" has invalid '
                                'value "%s".' % (featureId, featureValue))
                    elif featureId in featuresetRegionFeatures:
                        if featureValue not in [0, 2, 3]:
                            raise ValidationException(
                                'Annotation feature "%s" has invalid '
                                'value "%s".' % (featureId, featureValue))
                    else:
                        raise ValidationException(
                            'Annotation has invalid feature "%s".' % featureId)

        return super(Annotation, self).validate(doc)
