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
from girder.api.rest import Resource, RestException, loadmodel
from girder.api.describe import Description, describeRoute
from girder.constants import AccessType


class AnnotationResource(Resource):
    def __init__(self):
        super(AnnotationResource, self).__init__()
        self.resourceName = 'annotation'

        self.route('GET', (), self.find)
        self.route('GET', (':id',), self.getAnnotation)
        self.route('PUT', (':id',), self.submitAnnotation)

    @describeRoute(
        Description('Return a list of annotations.')
        .param('studyId', 'The ID of the study to filter by.',
               paramType='query', required=True)
        .param('userId', 'The ID of the user to filter by.',
               paramType='query', required=False)
        .param('segmentationId', 'The ID of the segmentation to filter by.',
               paramType='query', required=False)
        .param('imageId', 'The ID of the image to filter by.',
               paramType='query', required=False)
        .errorResponse()
    )
    @access.public
    def find(self, params):
        Study = self.model('study', 'isic_archive')

        self.requireParams(('studyId',), params)

        # check access here for simplicity
        study = Study.load(
            params['studyId'], user=self.getCurrentUser(),
            level=AccessType.READ, exc=True)

        annotatorUser = self.model('user').load(
            params['userId'], force=True, exc=True) \
            if 'userId' in params else None

        segmentation = self.model('segmentation', 'isic_archive').load(
            params['segmentationId'], exc=True) \
            if 'segmentationId' in params else None

        image = self.model('image', 'isic_archive').load(
            params['imageId'], force=True, exc=True) \
            if 'imageId' in params else None

        # TODO: add state

        # TODO: add limit, offset, sort

        # TODO: limit fields returned
        annotations = Study.childAnnotations(
            study=study,
            annotatorUser=annotatorUser,
            segmentation=segmentation,
            imageItem=image
        )

        return [
            {
                '_id': annotation['_id'],
                'name': annotation['name'],
                'studyId': annotation['meta']['studyId'],
                'userId': annotation['meta']['userId'],
                'segmentationId': annotation['meta']['segmentationId'],
                'imageId': annotation['meta']['imageId'],
                # TODO: change to State enum and ensure it serializes
                'state': 'complete' \
                         if annotation['meta']['stopTime'] is not None \
                         else 'active'
            }
            for annotation in annotations
        ]

    @describeRoute(
        Description('Get annotation details.')
        .param('id', 'The ID of the annotation to be fetched.',
               paramType='path')
        .errorResponse()
    )
    @access.public
    @loadmodel(model='annotation', plugin='isic_archive', level=AccessType.READ)
    def getAnnotation(self, annotation, params):
        output = {
            '_id': annotation['_id'],
            'name': annotation['name']
        }
        output.update(annotation['meta'])

        userSummaryFields = ['_id', 'login', 'firstName', 'lastName']
        output['user'] = self.model('user').load(
            output.pop('userId'),
            force=True, exc=True,
            fields=userSummaryFields)

        return output

    @describeRoute(
        Description('Submit a completed annotation.')
        .param('id', 'The ID of the annotation to be submitted.',
               paramType='path')
        .param('body', 'JSON containing the annotation parameters.',
               paramType='body', required=True)
        .errorResponse()
    )
    @access.user
    @loadmodel(model='annotation', plugin='isic_archive', level=AccessType.READ)
    def submitAnnotation(self, annotation, params):
        Study = self.model('study', 'isic_archive')
        if annotation['baseParentId'] != Study.loadStudyCollection()['_id']:
            raise RestException(
                'Annotation id references a non-annotation item.')

        if annotation['meta']['userId'] != self.getCurrentUser()['_id']:
            raise RestException('Current user does not own this annotation.')

        if annotation['meta'].get('stopTime'):
            raise RestException('Annotation is already complete.')

        bodyJson = self.getBodyJson()
        self.requireParams(('status', 'startTime', 'stopTime', 'annotations'),
                           bodyJson)

        annotation['meta']['status'] = bodyJson['status']
        annotation['meta']['startTime'] = \
            datetime.datetime.utcfromtimestamp(bodyJson['startTime'] / 1000.0)
        annotation['meta']['stopTime'] = \
            datetime.datetime.utcfromtimestamp(bodyJson['stopTime'] / 1000.0)
        annotation['meta']['annotations'] = bodyJson['annotations']

        self.model('annotation', 'isic_archive').save(annotation)
