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
import numpy
import six

from bson import ObjectId

from girder.models.item import Item
from girder.models.model_base import ValidationException, GirderException

from .image import Image
from .study import Study
from .user import User


class Annotation(Item):
    def createAnnotation(self, study, image, creatorUser,
                         annotatorFolder):
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
                'imageId': image['_id'],
                'startTime': None,
                'stopTime': None,
                'annotations': None
            }
        )
        return annotationItem

    def getState(self, annotation):
        return (Study().State.COMPLETE
                if annotation['meta'].get('stopTime') is not None
                else Study().State.ACTIVE)

    def _getImageMasks(self, annotation, featureId, image=None):
        if self.getState(annotation) != Study().State.COMPLETE:
            raise GirderException('Annotation is incomplete.')

        featureValues = annotation['meta']['annotations'].get(featureId, [])
        if not isinstance(featureValues, list):
            raise GirderException(
                'Feature %s is not a superpixel annotation.' % featureId)

        possibleSuperpixelNums = numpy.array([
            superpixelNum
            for superpixelNum, featureValue
            in enumerate(featureValues)
            if featureValue == 0.5
        ])
        definiteSuperpixelNums = numpy.array([
            superpixelNum
            for superpixelNum, featureValue
            in enumerate(featureValues)
            if featureValue == 1.0
        ])

        if not image:
            image = Image().load(annotation['meta']['imageId'], force=True, exc=True)
        superpixelsData = Image().superpixelsData(image)

        possibleMask = numpy.in1d(
            superpixelsData.flat,
            possibleSuperpixelNums
        ).reshape(superpixelsData.shape)
        possibleMask = possibleMask.astype(numpy.bool_)
        definiteMask = numpy.in1d(
            superpixelsData.flat,
            definiteSuperpixelNums
        ).reshape(superpixelsData.shape)
        definiteMask = definiteMask.astype(numpy.bool_)

        return possibleMask, definiteMask

    def renderAnnotation(self, annotation, featureId):
        image = Image().load(annotation['meta']['imageId'], force=True, exc=True)
        renderData = Image().imageData(image)

        possibleMask, definiteMask = self._getImageMasks(
            annotation, featureId, image)

        POSSIBLE_OVERLAY_COLOR = numpy.array([250, 250, 0])
        DEFINITE_OVERLAY_COLOR = numpy.array([0, 0, 255])

        renderData[possibleMask] = POSSIBLE_OVERLAY_COLOR
        renderData[definiteMask] = DEFINITE_OVERLAY_COLOR

        return renderData

    def _findQueryFilter(self, query):
        newQuery = query.copy() if query is not None else {}
        newQuery.update({
            'baseParentId': Study().loadStudyCollection()['_id']
        })
        return newQuery

    def find(self, query=None, **kwargs):
        annotationQuery = self._findQueryFilter(query)
        return super(Annotation, self).find(annotationQuery, **kwargs)

    def findOne(self, query=None, **kwargs):
        annotationQuery = self._findQueryFilter(query)
        return super(Annotation, self).findOne(annotationQuery, **kwargs)

    def filter(self, annotation, user=None, additionalKeys=None):
        output = {
            '_id': annotation['_id'],
            '_modelType': 'annotation',
            'studyId': annotation['meta']['studyId'],
            'image': Image().filterSummary(
                Image().load(annotation['meta']['imageId'], force=True, exc=True),
                user),
            'user': User().filterSummary(
                user=User().load(annotation['meta']['userId'], force=True, exc=True),
                accessorUser=user),
            'state': Annotation().getState(annotation)
        }
        if Annotation().getState(annotation) == Study().State.COMPLETE:
            output.update({
                'annotations': {
                    featureId:
                        featureValue
                        if not isinstance(featureValue, list) else
                        any(featureValue)
                    for featureId, featureValue in
                    six.viewitems(annotation['meta']['annotations'])
                },
                'status': annotation['meta']['status'],
                'startTime': annotation['meta']['startTime'],
                'stopTime': annotation['meta']['startTime'],
            })

        return output

    def filterSummary(self, annotation, user=None):
        return {
            '_id': annotation['_id'],
            'name': annotation['name'],
            'studyId': annotation['meta']['studyId'],
            'userId': annotation['meta']['userId'],
            'imageId': annotation['meta']['imageId'],
            'state': self.getState(annotation)
        }

    def validate(self, doc):  # noqa - C901
        # If annotation is fully created
        if doc.get('meta') and 'studyId' in doc['meta']:
            for field in ['studyId', 'userId', 'imageId']:
                if not isinstance(doc['meta'].get(field), ObjectId):
                    raise ValidationException(
                        'Annotation field "%s" must be an ObjectId' % field)

            study = Study().load(doc['meta']['studyId'], force=True, exc=False)
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
                featureset = Study().getFeatureset(study)
                featuresetGlobalFeatures = {
                    feature['id']: feature
                    for feature in
                    featureset['globalFeatures']
                }
                featuresetLocalFeatures = {
                    feature['id']: feature
                    for feature in
                    featureset['localFeatures']
                }
                if featuresetLocalFeatures:
                    image = Image().load(doc['meta']['imageId'], force=True)
                    superpixels = Image().superpixelsData(image)
                    maxSuperpixel = superpixels.max()
                else:
                    maxSuperpixel = None
                for featureId, featureValue in six.viewitems(
                        doc['meta']['annotations']):
                    if featureId in featuresetGlobalFeatures:
                        featureOptions = set(
                            option['id']
                            for option in
                            featuresetGlobalFeatures[featureId]['options'])
                        if featureValue not in featureOptions:
                            raise ValidationException(
                                'Annotation feature "%s" has invalid '
                                'value "%s".' % (featureId, featureValue))
                    elif featureId in featuresetLocalFeatures:
                        if not (
                            isinstance(featureValue, list) and
                            len(featureValue) == maxSuperpixel + 1 and
                            all(superpixelValue in [0.0, 0.5, 1.0]
                                for superpixelValue in featureValue)
                        ):
                            raise ValidationException(
                                'Annotation feature "%s" has invalid '
                                'value "%s".' % (featureId, featureValue))
                    else:
                        raise ValidationException(
                            'Annotation has invalid feature "%s".' % featureId)

        return super(Annotation, self).validate(doc)
