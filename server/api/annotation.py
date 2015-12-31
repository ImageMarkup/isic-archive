#!/usr/bin/env python
# -*- coding: utf-8 -*-

import collections
import datetime
import json

from bson import ObjectId
import pymongo

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

        self.route('GET', (':annotation_id',), self.getAnnotation)
        self.route('PUT', (':annotation_id',), self.submitAnnotation)


    @describeRoute(
        Description('Get annotation details.')
        .param('annotation_id', 'The ID of the annotation to be fetched.', paramType='path')
        .errorResponse()
    )
    @access.public
    @loadmodel(model='annotation', plugin='isic_archive', map={'annotation_id': 'annotation_item'}, level=AccessType.READ)
    def getAnnotation(self, annotation_item, params):
        image = self.model('image', 'isic_archive').load(
            annotation_item['meta']['imageId'], force=True)
        # segmentation = self.model('segmentation', 'isic_archive').load(
        #     annotation_item['meta']['segmentationId'], force=True)
        study = self.model('study', 'isic_archive').load(
            annotation_item['meta']['studyId'], force=True)
        featureset = self.model('featureset', 'isic_archive').load(
            study['meta']['featuresetId'])

        return_dict = {
            'image': image,
            'segmentationId': annotation_item['meta']['segmentationId']
        }

        # transform featureset to legacy format
        legacy_featureset = dict()
        for new_level, legacy_level in [
                ('image_features', 'lesionlevel'),
                ('region_features', 'tiles')
                ]:
            # need to first build an intermediate variable to maintain ordering
            legacy_questions = collections.OrderedDict()

            for feature in featureset[new_level]:
                header = feature['name'][0]
                legacy_question = {
                    'name': feature['name'][0] if len(feature['name']) == 1 else ': '.join(feature['name'][1:]),
                    'type': feature['type']
                }
                if feature['type'] == 'select':
                    legacy_question['shortname'] = feature['id']
                    legacy_question['options'] = feature['options']
                else:
                    legacy_question['id'] = feature['id']
                legacy_questions.setdefault(header, list()).append(legacy_question)

            legacy_featureset[legacy_level] = [
                {'header': header, 'questions': questions}
                for header, questions in legacy_questions.iteritems()
            ]
        return_dict['features'] = legacy_featureset

        return return_dict


    @describeRoute(
        Description('Submit a completed annotation.')
        .param('annotation_id', 'The ID of the annotation to be submitted.', paramType='path')
        .param('body', 'JSON containing the annotation parameters.', paramType='body', required=True)
        .errorResponse()
    )
    @access.user
    @loadmodel(model='annotation', plugin='isic_archive', map={'annotation_id': 'annotation_item'}, level=AccessType.READ)
    def submitAnnotation(self, annotation_item, params):
        if annotation_item['baseParentId'] != ISIC.AnnotationStudies.collection['_id']:
            raise RestException('Annotation id references a non-annotation item.')

        if annotation_item['meta']['userId'] != self.getCurrentUser()['_id']:
            raise RestException('Current user does not own this annotation.')

        if annotation_item['meta'].get('stopTime'):
            raise RestException('Annotation is already complete.')

        body_json = self.getBodyJson()
        self.requireParams(('status', 'imageId', 'startTime', 'stopTime', 'annotations'), body_json)

        if ObjectId(body_json['imageId']) != annotation_item['meta']['imageId']:
            raise RestException('Submitted imageId is incorrect.')

        annotation_item['meta']['status'] = body_json['status']
        annotation_item['meta']['startTime'] = \
            datetime.datetime.utcfromtimestamp(body_json['startTime'] / 1000.0)
        annotation_item['meta']['stopTime'] = \
            datetime.datetime.utcfromtimestamp(body_json['stopTime'] / 1000.0)
        annotation_item['meta']['annotations'] = body_json['annotations']

        self.model('annotation', 'isic_archive').save(annotation_item)
