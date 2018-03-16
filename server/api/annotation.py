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

from girder.api import access
from girder.api.rest import loadmodel, setRawResponse, setResponseHeader
from girder.api.describe import Description, describeRoute
from girder.constants import AccessType
from girder.exceptions import RestException, ValidationException

from .base import IsicResource
from ..models.annotation import Annotation
from ..models.image import Image
from ..models.segmentation_helpers import ScikitSegmentationHelper
from ..models.study import Study
from ..models.user import User


class AnnotationResource(IsicResource):
    def __init__(self):
        super(AnnotationResource, self).__init__()
        self.resourceName = 'annotation'

        self.route('GET', (), self.find)
        self.route('GET', (':annotationId',), self.getAnnotation)
        self.route('GET', (':annotationId', 'markup', ':featureId'),
                   self.getAnnotationMarkupMask)
        self.route('GET', (':annotationId', 'markup', ':featureId', 'rendered'),
                   self.getAnnotationMarkupRendered)
        self.route('GET', (':annotationId', 'markup', ':featureId', 'superpixels'),
                   self.getAnnotationMarkupSuperpixels)
        self.route('PUT', (':annotationId',), self.submitAnnotation)

        # TODO: These are all deprecated
        self.route('GET', (':annotationId', ':featureId'),
                   self.getAnnotationMarkupSuperpixels)
        self.route('GET', (':annotationId', ':featureId', 'mask'),
                   self.getAnnotationMarkupMask)
        self.route('GET', (':annotationId', ':featureId', 'render'),
                   self.getAnnotationMarkupRendered)

    @describeRoute(
        Description('Return a list of annotations.')
        .param('studyId', 'The ID of the study to filter by.', paramType='query', required=True)
        .param('userId', 'The ID of the user to filter by.', paramType='query', required=False)
        .param('imageId', 'The ID of the image to filter by.', paramType='query', required=False)
        .param('state', 'Filter annotations to those at a given state.', paramType='query',
               required=False, enum=('active', 'complete'))
        .param('detail', 'Display the full information for each annotation, instead of a summary.',
               required=False, dataType='boolean', default=False)
        .errorResponse()
    )
    @access.cookie
    @access.public
    def find(self, params):
        self.requireParams(['studyId'], params)

        # check access here for simplicity
        study = Study().load(
            params['studyId'], user=self.getCurrentUser(),
            level=AccessType.READ, exc=True)

        annotatorUser = User().load(
            params['userId'], force=True, exc=True) \
            if 'userId' in params else None

        image = Image().load(
            params['imageId'], force=True, exc=True) \
            if 'imageId' in params else None

        state = None
        if 'state' in params:
            state = params['state']
            if state not in {Study().State.ACTIVE, Study().State.COMPLETE}:
                raise ValidationException('Value may only be "active" or "complete".', 'state')

        detail = self.boolParam('detail', params, default=False)
        filterFunc = Annotation().filter if detail else Annotation().filterSummary

        # TODO: add limit, offset, sort
        return [
            filterFunc(annotation)
            for annotation in
            Study().childAnnotations(
                study=study,
                annotatorUser=annotatorUser,
                image=image,
                state=state
            )
        ]

    @describeRoute(
        Description('Get annotation details.')
        .param('annotationId', 'The ID of the annotation to be fetched.', paramType='path')
        .errorResponse()
    )
    @access.cookie
    @access.public
    @loadmodel(map={'annotationId': 'annotation'}, model='annotation', plugin='isic_archive',
               level=AccessType.READ)
    def getAnnotation(self, annotation, params):
        user = self.getCurrentUser()
        return Annotation().filter(annotation, user)

    @describeRoute(
        Description('Return an annotation\'s markup as a raw superpixel array.')
        .param('annotationId', 'The ID of the annotation.', paramType='path')
        .param('featureId', 'The feature ID for the markup.', paramType='path')
        .errorResponse()
    )
    @access.cookie
    @access.public
    @loadmodel(map={'annotationId': 'annotation'}, model='annotation', plugin='isic_archive',
               level=AccessType.READ)
    def getAnnotationMarkupSuperpixels(self, annotation, featureId, params):
        study = Study().load(annotation['studyId'], force=True, exc=True)

        if not any(featureId == feature['id'] for feature in study['meta']['features']):
            raise ValidationException('That featureId is not present in the study.', 'featureId')
        if Annotation().getState(annotation) != Study().State.COMPLETE:
            raise RestException('Only complete annotations have markup.')

        featureValues = annotation['markups'].get(featureId, [])
        return featureValues

    @describeRoute(
        Description('Return an annotation\'s markup as a mask.')
        .param('annotationId', 'The ID of the annotation.', paramType='path')
        .param('featureId', 'The feature ID for the markup.', paramType='path')
        .produces('image/png')
        .errorResponse()
    )
    @access.cookie
    @access.public
    @loadmodel(map={'annotationId': 'annotation'}, model='annotation', plugin='isic_archive',
               level=AccessType.READ)
    def getAnnotationMarkupMask(self, annotation, featureId, params):
        study = Study().load(annotation['studyId'], force=True, exc=True)

        if not any(featureId == feature['id'] for feature in study['meta']['features']):
            raise ValidationException('That featureId is not present in the study.', 'featureId')
        if Annotation().getState(annotation) != Study().State.COMPLETE:
            raise RestException('Only complete annotations have markup.')

        renderData = Annotation().maskMarkup(annotation, featureId)

        renderEncodedStream = ScikitSegmentationHelper.writeImage(renderData, 'png')
        renderEncodedData = renderEncodedStream.getvalue()

        # Only setRawResponse now, as this handler may return a JSON error earlier
        setRawResponse()
        setResponseHeader('Content-Type', 'image/png')
        contentName = '%s_%s_annotation.png' % (
            annotation['_id'],
            featureId.replace('/', ',')  # TODO: replace with a better character
        )
        setResponseHeader(
            'Content-Disposition',
            'inline; filename="%s"' % contentName)
        setResponseHeader('Content-Length', len(renderEncodedData))

        return renderEncodedData

    @describeRoute(
        Description('Render an annotation\'s markup, overlaid on its image.')
        .param('annotationId', 'The ID of the annotation to be rendered.', paramType='path')
        .param('featureId', 'The feature ID for the markup.', paramType='path')
        .param('contentDisposition',
               'Specify the Content-Disposition response header disposition-type value.',
               required=False, enum=['inline', 'attachment'])
        .produces('image/jpeg')
        .errorResponse()
    )
    @access.cookie
    @access.public
    @loadmodel(map={'annotationId': 'annotation'}, model='annotation', plugin='isic_archive',
               level=AccessType.READ)
    def getAnnotationMarkupRendered(self, annotation, featureId, params):
        contentDisp = params.get('contentDisposition', None)
        if contentDisp is not None and contentDisp not in {'inline', 'attachment'}:
            raise ValidationException('Unallowed contentDisposition type "%s".' % contentDisp,
                                      'contentDisposition')

        study = Study().load(annotation['studyId'], force=True, exc=True)

        if not any(featureId == feature['id'] for feature in study['meta']['features']):
            raise ValidationException('That featureId is not present in the study.', 'featureId')
        if Annotation().getState(annotation) != Study().State.COMPLETE:
            raise RestException('Only complete annotations have markup.')

        renderData = Annotation().renderMarkup(annotation, featureId)

        renderEncodedStream = ScikitSegmentationHelper.writeImage(renderData, 'jpeg')
        renderEncodedData = renderEncodedStream.getvalue()

        # Only setRawResponse now, as this handler may return a JSON error earlier
        setRawResponse()
        setResponseHeader('Content-Type', 'image/jpeg')
        contentName = '%s_%s_annotation.jpg' % (
            annotation['_id'],
            featureId.replace('/', ',')  # TODO: replace with a better character
        )
        if contentDisp == 'inline':
            setResponseHeader(
                'Content-Disposition',
                'inline; filename="%s"' % contentName)
        else:
            setResponseHeader(
                'Content-Disposition',
                'attachment; filename="%s"' % contentName)
        setResponseHeader('Content-Length', len(renderEncodedData))

        return renderEncodedData

    @describeRoute(
        Description('Submit a completed annotation.')
        .param('annotationId', 'The ID of the annotation to be submitted.', paramType='path')
        .param('body', 'JSON containing the annotation parameters.',
               paramType='body', required=True)
        .errorResponse()
    )
    @access.user
    @loadmodel(map={'annotationId': 'annotation'}, model='annotation', plugin='isic_archive',
               level=AccessType.READ)
    def submitAnnotation(self, annotation, params):
        if annotation['userId'] != self.getCurrentUser()['_id']:
            raise RestException('Current user does not own this annotation.')

        if annotation.get('stopTime'):
            raise RestException('Annotation is already complete.')

        bodyJson = self.getBodyJson()
        self.requireParams(['status', 'startTime', 'stopTime', 'responses', 'markups'], bodyJson)

        annotation['status'] = bodyJson['status']
        annotation['startTime'] = datetime.datetime.utcfromtimestamp(
            bodyJson['startTime'] / 1000.0)
        annotation['stopTime'] = datetime.datetime.utcfromtimestamp(
            bodyJson['stopTime'] / 1000.0)
        annotation['responses'] = bodyJson['responses']
        annotation['markups'] = bodyJson['markups']

        Annotation().save(annotation)
