#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime

from girder.api import access
from girder.api.rest import Resource, RestException, loadmodel
from girder.api.describe import Description, describeRoute
from girder.constants import AccessType

from ..provision_utility import ISIC


class AnnotationResource(Resource):
    def __init__(self, plugin_root_dir):
        super(AnnotationResource, self).__init__()
        self.resourceName = 'annotation'
        self.plugin_root_dir = plugin_root_dir

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

        annotator_user = self.model('user').load(
            params['userId'], force=True, exc=True) \
            if 'userId' in params else None

        segmentation = self.model('segmentation', 'isic_archive').load(
            params['segmentationId'], force=True, exc=True) \
            if 'segmentationId' in params else None

        image = self.model('image', 'isic_archive').load(
            params['imageId'], force=True, exc=True) \
            if 'imageId' in params else None

        # TODO: add state

        # TODO: add limit, offset

        # TODO: limit fields returned
        annotations = Study.childAnnotations(
            study=study,
            annotator_user=annotator_user,
            segmentation=segmentation,
            image_item=image
        )

        return list(
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
        )


    @describeRoute(
        Description('Get annotation details.')
        .param('annotation_id', 'The ID of the annotation to be fetched.', paramType='path')
        .errorResponse()
    )
    @access.public
    @loadmodel(model='annotation', plugin='isic_archive', level=AccessType.READ)
    def getAnnotation(self, annotation, params):

        return_dict = {
            '_id': annotation['_id'],
            'name': annotation['name']
        }
        return_dict.update(annotation['meta'])

        userSummaryFields = ['_id', 'login', 'firstName', 'lastName']
        return_dict['user'] = self.model('user').load(
            return_dict.pop('userId'),
            force=True, exc=True,
            fields=userSummaryFields)
        # Deal with a bug in Girder
        # TODO: Remove this
        import six
        return_dict['user'] = {
            k: v
            for k, v in six.viewitems(return_dict['user'])
            if k in userSummaryFields
        }

        return return_dict


    @describeRoute(
        Description('Submit a completed annotation.')
        .param('annotation_id', 'The ID of the annotation to be submitted.', paramType='path')
        .param('body', 'JSON containing the annotation parameters.', paramType='body', required=True)
        .errorResponse()
    )
    @access.user
    @loadmodel(model='annotation', plugin='isic_archive', level=AccessType.READ)
    def submitAnnotation(self, annotation, params):
        if annotation['baseParentId'] != ISIC.AnnotationStudies.collection['_id']:
            raise RestException('Annotation id references a non-annotation item.')

        if annotation['meta']['userId'] != self.getCurrentUser()['_id']:
            raise RestException('Current user does not own this annotation.')

        if annotation['meta'].get('stopTime'):
            raise RestException('Annotation is already complete.')

        body_json = self.getBodyJson()
        self.requireParams(('status', 'startTime', 'stopTime', 'annotations'), body_json)

        annotation['meta']['status'] = body_json['status']
        annotation['meta']['startTime'] = \
            datetime.datetime.utcfromtimestamp(body_json['startTime'] / 1000.0)
        annotation['meta']['stopTime'] = \
            datetime.datetime.utcfromtimestamp(body_json['stopTime'] / 1000.0)
        annotation['meta']['annotations'] = body_json['annotations']

        self.model('annotation', 'isic_archive').save(annotation)
