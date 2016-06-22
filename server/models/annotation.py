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

from girder.constants import AccessType
from girder.models.item import Item as ItemModel


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

    def validate(self, doc):
        # TODO: implement
        # raise ValidationException
        return super(Annotation, self).validate(doc)
