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
from girder.api.rest import RestException, loadmodel, setRawResponse, setResponseHeader
from girder.api.describe import Description, describeRoute
from girder.constants import AccessType
from girder.models.model_base import ValidationException

from .base import IsicResource
from ..models.segmentation_helpers import ScikitSegmentationHelper


class AnnotationResource(IsicResource):
    def __init__(self):
        super(AnnotationResource, self).__init__()
        self.resourceName = 'annotation'

        self.route('GET', (), self.find)
        self.route('GET', (':id',), self.getAnnotation)
        self.route('GET', (':id', 'render'), self.renderAnnotation)
        self.route('PUT', (':id',), self.submitAnnotation)

    @describeRoute(
        Description('Return a list of annotations.')
        .param('studyId', 'The ID of the study to filter by.', paramType='query', required=True)
        .param('userId', 'The ID of the user to filter by.', paramType='query', required=False)
        .param('imageId', 'The ID of the image to filter by.', paramType='query', required=False)
        .errorResponse()
    )
    @access.cookie
    @access.public
    def find(self, params):
        Annotation = self.model('annotation', 'isic_archive')
        Image = self.model('image', 'isic_archive')
        Study = self.model('study', 'isic_archive')
        User = self.model('user', 'isic_archive')

        self.requireParams(['studyId'], params)

        # check access here for simplicity
        study = Study.load(
            params['studyId'], user=self.getCurrentUser(),
            level=AccessType.READ, exc=True)

        annotatorUser = User.load(
            params['userId'], force=True, exc=True) \
            if 'userId' in params else None

        image = Image.load(
            params['imageId'], force=True, exc=True) \
            if 'imageId' in params else None

        # TODO: add state

        # TODO: add limit, offset, sort

        # TODO: limit fields returned
        annotations = Study.childAnnotations(
            study=study,
            annotatorUser=annotatorUser,
            image=image
        )

        return [
            {
                '_id': annotation['_id'],
                'name': annotation['name'],
                'studyId': annotation['meta']['studyId'],
                'userId': annotation['meta']['userId'],
                'imageId': annotation['meta']['imageId'],
                'state': Annotation.getState(annotation)
            }
            for annotation in annotations
        ]

    @describeRoute(
        Description('Get annotation details.')
        .param('id', 'The ID of the annotation to be fetched.', paramType='path')
        .errorResponse()
    )
    @access.cookie
    @access.public
    @loadmodel(model='annotation', plugin='isic_archive', level=AccessType.READ)
    def getAnnotation(self, annotation, params):
        Annotation = self.model('annotation', 'isic_archive')
        Image = self.model('image', 'isic_archive')
        Study = self.model('study', 'isic_archive')
        User = self.model('user', 'isic_archive')

        currentUser = self.getCurrentUser()

        output = {
            '_id': annotation['_id'],
            '_modelType': 'annotation',
            'studyId': annotation['meta']['studyId'],
            'image': Image.filterSummary(
                Image.load(annotation['meta']['imageId'], force=True, exc=True),
                currentUser),
            'user': User.filterSummary(
                user=User.load(annotation['meta']['userId'], force=True, exc=True),
                accessorUser=currentUser),
            'state': Annotation.getState(annotation)
        }
        if Annotation.getState(annotation) == Study.State.COMPLETE:
            output.update({
                'annotations': annotation['meta']['annotations'],
                'status': annotation['meta']['status'],
                'startTime': annotation['meta']['startTime'],
                'stopTime': annotation['meta']['startTime'],
            })

        return output

    @describeRoute(
        Description('Render an annotation feature, overlaid on its image.')
        .param('id', 'The ID of the annotation to be rendered.', paramType='path')
        .param('featureId', 'The feature ID to be rendered.', paramType='query', required=True)
        .param('contentDisposition',
               'Specify the Content-Disposition response header disposition-type value.',
               required=False, enum=['inline', 'attachment'])
        .produces('image/jpeg')
        .errorResponse()
    )
    @access.cookie
    @access.public
    @loadmodel(model='annotation', plugin='isic_archive', level=AccessType.READ)
    def renderAnnotation(self, annotation, params):
        Study = self.model('study', 'isic_archive')
        Annotation = self.model('annotation', 'isic_archive')
        contentDisp = params.get('contentDisposition', None)
        if contentDisp is not None and contentDisp not in {'inline', 'attachment'}:
            raise ValidationException('Unallowed contentDisposition type "%s".' % contentDisp,
                                      'contentDisposition')

        self.requireParams(['featureId'], params)
        featureId = params['featureId']

        study = Study.load(annotation['meta']['studyId'], force=True, exc=True)
        featureset = Study.getFeatureset(study)

        if not any(featureId == feature['id'] for feature in featureset['localFeatures']):
            raise ValidationException('Invalid featureId.', 'featureId')
        if Annotation.getState(annotation) != Study.State.COMPLETE:
            raise RestException('Only complete annotations can be rendered.')

        renderData = Annotation.renderAnnotation(annotation, featureId)

        renderEncodedStream = ScikitSegmentationHelper.writeImage(renderData, 'jpeg')
        renderEncodedData = renderEncodedStream.getvalue()

        # Only setRawResponse now, as this handler may return a JSON error
        # earlier
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
        .param('id', 'The ID of the annotation to be submitted.', paramType='path')
        .param('body', 'JSON containing the annotation parameters.',
               paramType='body', required=True)
        .errorResponse()
    )
    @access.user
    @loadmodel(model='annotation', plugin='isic_archive', level=AccessType.READ)
    def submitAnnotation(self, annotation, params):
        Annotation = self.model('annotation', 'isic_archive')
        Study = self.model('study', 'isic_archive')

        if annotation['baseParentId'] != Study.loadStudyCollection()['_id']:
            raise RestException('Annotation id references a non-annotation item.')

        if annotation['meta']['userId'] != self.getCurrentUser()['_id']:
            raise RestException('Current user does not own this annotation.')

        if annotation['meta'].get('stopTime'):
            raise RestException('Annotation is already complete.')

        bodyJson = self.getBodyJson()
        self.requireParams(['status', 'startTime', 'stopTime', 'annotations'], bodyJson)

        annotation['meta']['status'] = bodyJson['status']
        annotation['meta']['startTime'] = datetime.datetime.utcfromtimestamp(
            bodyJson['startTime'] / 1000.0)
        annotation['meta']['stopTime'] = datetime.datetime.utcfromtimestamp(
            bodyJson['stopTime'] / 1000.0)
        annotation['meta']['annotations'] = bodyJson['annotations']

        Annotation.save(annotation)
