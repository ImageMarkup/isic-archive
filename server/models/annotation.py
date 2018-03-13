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

from girder.exceptions import GirderException, ValidationException
from girder.models.model_base import Model
from girder.utility.acl_mixin import AccessControlMixin

from .image import Image
from .study import Study
from .user import User


class Annotation(AccessControlMixin, Model):
    def initialize(self):
        self.name = 'annotation'
        self.ensureIndices(['studyId', 'imageId', 'userId'])

        # TODO: resourceColl should be ['study', 'isic_archive'], but upstream support is unclear
        self.resourceColl = 'folder'
        self.resourceParent = 'studyId'

    def createAnnotation(self, study, image, user):
        annotation = self.save({
            'studyId': study['_id'],
            'imageId': image['_id'],
            'userId': user['_id'],
            'startTime': None,
            'stopTime': None,
            'status': None,
            'responses': {},
            'markups': {},
        })

        return annotation

    def getState(self, annotation):
        return (Study().State.COMPLETE
                if annotation['stopTime'] is not None
                else Study().State.ACTIVE)

    def _getImageMasks(self, annotation, featureId, image=None):
        if self.getState(annotation) != Study().State.COMPLETE:
            raise GirderException('Annotation is incomplete.')

        featureValues = annotation['markups'].get(featureId, [])
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
            image = Image().load(annotation['imageId'], force=True, exc=True)
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

    def maskMarkup(self, annotation, featureId):
        possibleMask, definiteMask = self._getImageMasks(annotation, featureId)

        renderedMask = numpy.zeros(possibleMask.shape, dtype=numpy.uint)
        renderedMask[possibleMask] = 128
        renderedMask[definiteMask] = 255

        return renderedMask

    def renderMarkup(self, annotation, featureId):
        image = Image().load(annotation['imageId'], force=True, exc=True)
        renderData = Image().imageData(image)

        possibleMask, definiteMask = self._getImageMasks(
            annotation, featureId, image)

        POSSIBLE_OVERLAY_COLOR = numpy.array([250, 250, 0])
        DEFINITE_OVERLAY_COLOR = numpy.array([0, 0, 255])

        renderData[possibleMask] = POSSIBLE_OVERLAY_COLOR
        renderData[definiteMask] = DEFINITE_OVERLAY_COLOR

        return renderData

    def filter(self, annotation, user=None, additionalKeys=None):
        output = {
            '_id': annotation['_id'],
            '_modelType': 'annotation',
            'studyId': annotation['studyId'],
            'image': Image().filterSummary(
                Image().load(annotation['imageId'], force=True, exc=True),
                user),
            'user': User().filterSummary(
                user=User().load(annotation['userId'], force=True, exc=True),
                accessorUser=user),
            'state': Annotation().getState(annotation)
        }
        if Annotation().getState(annotation) == Study().State.COMPLETE:
            boolMarkups = {
                featureId: any(markup)
                for featureId, markup
                in six.viewitems(annotation['markups'])
            }

            output.update({
                # TODO: "annotations" is deprecated and will be removed
                'annotations': dict(
                    annotation['responses'],
                    **boolMarkups
                ),
                'status': annotation['status'],
                'startTime': annotation['startTime'],
                'stopTime': annotation['stopTime'],
                'responses': annotation['responses'],
                'markups': boolMarkups
            })

        return output

    def filterSummary(self, annotation, user=None):
        return {
            '_id': annotation['_id'],
            'studyId': annotation['studyId'],
            'userId': annotation['userId'],
            'imageId': annotation['imageId'],
            'state': self.getState(annotation)
        }

    def validate(self, doc):  # noqa - C901
        for field in ['studyId', 'userId', 'imageId']:
            if not isinstance(doc.get(field), ObjectId):
                raise ValidationException('Annotation field "%s" must be an ObjectId' % field)

        study = Study().load(doc['studyId'], force=True, exc=False)
        if not study:
            raise ValidationException(
                'Annotation field "studyId" must reference an existing Study.')

        # If annotation is complete
        if doc.get('stopTime'):
            if not isinstance(doc.get('status'), six.string_types):
                raise ValidationException('Annotation field "status" must be a string.')
            for field in ['startTime', 'stopTime']:
                if not isinstance(doc.get(field), datetime.datetime):
                    raise ValidationException('Annotation field "%s" must be a datetime.' % field)

            featureset = Study().getFeatureset(study)
            featuresetQuestions = {
                question['id']: question
                for question in featureset['globalFeatures']
            }
            featuresetFeatures = {
                feature['id']: feature
                for feature in featureset['localFeatures']
            }
            if featuresetFeatures:
                image = Image().load(doc['imageId'], force=True)
                superpixels = Image().superpixelsData(image)
                maxSuperpixel = superpixels.max()
            else:
                maxSuperpixel = None

            # Validate responses
            if not isinstance(doc.get('responses'), dict):
                raise ValidationException('Annotation field "responses" must be a mapping (dict).')
            try:
                for questionId, response in six.viewitems(doc['responses']):
                    if questionId not in featuresetQuestions:
                        raise ValidationException(
                            'Annotation has invalid question "%s".' % questionId)
            except ValidationException as e:
                # New-style annotation submissions index content by featureset names, not id, so
                # try to remap from these
                featuresetQuestionIdsByName = {
                    ' : '.join(question['name']): question['id']
                    for question in six.itervalues(featuresetQuestions)
                }
                try:
                    doc['responses'] = {
                        # This lookup in featuresetQuestionIdsByName may raise a KeyError
                        featuresetQuestionIdsByName[questionName]: response
                        for questionName, response in six.viewitems(doc['responses'])
                    }
                except KeyError:
                    # Re-raise the original failure, for a cleaner error message
                    raise e
            for questionId, response in six.viewitems(doc['responses']):
                questionOptions = set(
                    option['id']
                    for option in featuresetQuestions[questionId]['options']
                )
                try:
                    if response not in questionOptions:
                        raise ValidationException(
                            'Annotation question "%s" has invalid response "%s".' %
                            (questionId, response))
                except ValidationException:
                    # New-style annotation submissions have responses as option / choice names, not
                    # ids, so try to remap from these
                    questionOptionIdsByName = {
                        option['name']: option['id']
                        for option in featuresetQuestions[questionId]['options']
                    }
                    if response in questionOptionIdsByName:
                        doc['responses'][questionId] = questionOptionIdsByName[response]
                    else:
                        # Re-raise the original failure, for a cleaner error message
                        raise

            # Validate markups
            if not isinstance(doc.get('markups'), dict):
                raise ValidationException('Annotation field "markups" must be a mapping (dict).')
            try:
                for featureId, markup in six.viewitems(doc['markups']):
                    if featureId not in featuresetFeatures:
                        raise ValidationException(
                            'Annotation has invalid feature "%s".' % featureId)
            except ValidationException as e:
                # New-style annotation submissions index content by featureset names, not id, so
                # try to remap from these
                featuresetFeatureIdsByName = {
                    ' : '.join(feature['name']): feature['id']
                    for feature in six.itervalues(featuresetFeatures)
                }
                try:
                    doc['markups'] = {
                        # This lookup in featuresetFeatureIdsByName may raise a KeyError
                        featuresetFeatureIdsByName[featureName]: markup
                        for featureName, markup in six.viewitems(doc['markups'])
                    }
                except KeyError:
                    # Re-raise the original failure, for a cleaner error message
                    raise e
            for featureId, markup in six.viewitems(doc['markups']):
                if not (
                    isinstance(markup, list) and
                    len(markup) == maxSuperpixel + 1 and
                    all(superpixelValue in [0.0, 0.5, 1.0]
                        for superpixelValue in markup)
                ):
                    raise ValidationException(
                        'Annotation feature "%s" has invalid markup "%s".' % (featureId, markup))

        return doc
