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

        self.route('GET', (':id',), self.getAnnotation)
        self.route('PUT', (':id',), self.submitAnnotation)


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
