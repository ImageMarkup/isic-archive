#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime

from girder.api import access
from girder.api.rest import Resource, RestException, loadmodel
from girder.api.describe import Description
from girder.constants import AccessType

from ..provision_utility import ISIC


class AnnotationResource(Resource):
    def __init__(self,):
        self.resourceName = 'annotation'

        self.route('PUT', (':annotation_id',), self.submitAnnotation)


    @access.admin
    @loadmodel(model='item', map={'annotation_id': 'annotation_item'}, level=AccessType.READ)
    def submitAnnotation(self, annotation_item, params):
        if annotation_item['baseParentId'] != ISIC.AnnotationStudies.collection['_id']:
            raise RestException('Annotation id references a non-annotation item.')

        if annotation_item['meta']['userId'] != self.getCurrentUser():
            raise RestException('Current user does not own this annotation.')

        if annotation_item['meta'].get('stopTime'):
            raise RestException('Annotation is already complete.')

        body_json = self.getBodyJson()
        self.requireParams(('imageId', 'startTime', 'stopTime', 'annotations'), body_json)

        if body_json['imageId'] != annotation_item['meta']['imageId']:
            raise RestException('Submitted imageId is incorrect.')

        annotation_item['meta']['startTime'] = \
            datetime.datetime.utcfromtimestamp(annotation_item['startTime'] / 1000.0)
        annotation_item['meta']['stopTime'] = \
            datetime.datetime.utcfromtimestamp(annotation_item['stopTime'] / 1000.0)
        annotation_item['meta']['annotations'] = body_json['annotations']

        self.model('item').save(annotation_item)

    submitAnnotation.description = (
        Description('Submit a completed annotation.')
        .param('body', 'JSON containing the annotation parameters.', paramType='body')
        .errorResponse())
