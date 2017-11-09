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
from girder.exceptions import GirderException, ValidationException

from .feature import MASTER_FEATURES
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
                'responses': None
            }
        )
        return annotationItem

    def getState(self, annotation):
        return (Study().State.COMPLETE
                if annotation['meta'].get('stopTime') is not None
                else Study().State.ACTIVE)

    def _getImageMasks(self, annotation, responseId, image=None):
        if self.getState(annotation) != Study().State.COMPLETE:
            raise GirderException('Annotation is incomplete.')

        if MASTER_FEATURES[responseId]['type'] != 'superpixel':
            raise GirderException('Response %s type is not superpixels.' % responseId)
        try:
            responseValue = annotation['meta']['responses'][responseId]
        except KeyError:
            # If the response is missing, it may simply be absent, or may be invalid for this study
            study = Study().load(annotation['meta']['studyId'], force=True, exc=True)
            if responseId in study['meta']['featureIds']:
                responseValue = []
            else:
                raise GirderException(
                    'Response %s does not correspond to a feature in the study.' % responseId)


        possibleSuperpixelNums = numpy.array([
            superpixelNum
            for superpixelNum, superpixelValue
            in enumerate(responseValue)
            if superpixelValue == 0.5
        ])
        definiteSuperpixelNums = numpy.array([
            superpixelNum
            for superpixelNum, superpixelValue
            in enumerate(responseValue)
            if superpixelValue == 1.0
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

    def renderResponse(self, annotation, responseId):
        possibleMask, definiteMask = self._getImageMasks(annotation, responseId)

        renderedMask = numpy.zeros(possibleMask.shape, dtype=numpy.uint)
        renderedMask[possibleMask] = 128
        renderedMask[definiteMask] = 255

        return renderedMask

    def renderAnnotation(self, annotation, responseId):
        image = Image().load(annotation['meta']['imageId'], force=True, exc=True)
        renderData = Image().imageData(image)

        possibleMask, definiteMask = self._getImageMasks(annotation, responseId, image)

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

                if not isinstance(doc['meta'].get('responses'), dict):
                    raise ValidationException(
                        'Annotation field "responses" must be a mapping (dict).')

                # maxSuperpixel will be looked up and cached if necessary
                maxSuperpixel = None
                for responseId, responseValue in six.viewitems(doc['meta']['responses']):
                    try:
                        featureInfo = MASTER_FEATURES[responseId]
                    except KeyError:
                        raise ValidationException(
                            'Annotation has invalid response "%s".' % responseId)

                    if featureInfo['type'] == 'select':
                        featureOptions = set(option['id'] for option in featureInfo['options'])
                        if responseValue not in featureOptions:
                            raise ValidationException(
                                'Annotation response "%s" has invalid value "%s".' %
                                (responseId, responseValue))
                    elif featureInfo['type'] == 'superpixel':
                        if maxSuperpixel is None:
                            image = Image().load(doc['meta']['imageId'], force=True)
                            superpixels = Image().superpixelsData(image)
                            maxSuperpixel = superpixels.max()
                        if not (
                            isinstance(responseValue, list) and
                            len(responseValue) == maxSuperpixel + 1 and
                            all(superpixelValue in [0.0, 0.5, 1.0]
                                for superpixelValue in responseValue)
                        ):
                            raise ValidationException(
                                'Annotation response "%s" has invalid value "%s".' %
                                (responseId, responseValue))

        return super(Annotation, self).validate(doc)
