#!/usr/bin/env python
# -*- coding: utf-8 -*-

import csv
from cStringIO import StringIO
import functools
import itertools

import cherrypy
import pymongo

from girder.api import access
from girder.api.rest import Resource, RestException, loadmodel
from girder.api.describe import Description, describeRoute
from girder.constants import AccessType

from ..provision_utility import ISIC


class StudyResource(Resource):
    def __init__(self,):
        super(StudyResource, self).__init__()
        self.resourceName = 'study'

        self.route('GET', (), self.find)
        self.route('GET', (':id',), self.getStudy)
        self.route('GET', (':id', 'user'), self.getStudyUsers)
        self.route('GET', (':id', 'segmentation'), self.getStudySegmentations)
        self.route('GET', (':id', 'image'), self.getStudyImages)
        self.route('GET', (':id', 'task'), self.redirectTask)
        self.route('POST', (), self.createStudy)


    @describeRoute(
        Description('Return a list of annotation studies.')
        .param('state', 'Filter studies to those at a given state',
               paramType='query', required=False, enum=('active', 'complete'))
        .param('user', 'Filter studies to those containing a user ID, or "me".',
               paramType='query', required=False)
        .errorResponse()
    )
    @access.public
    def find(self, params):
        Study = self.model('study', 'isic_archive')

        limit, offset, sort = self.getPagingParameters(params, 'lowerName')

        annotator_user = None
        if params.get('user'):
            if params['user'] == 'me':
                annotator_user = self.getCurrentUser()
            else:
                annotator_user = self.model('user').load(
                    id=params['user'],
                    level=AccessType.READ,
                    user=self.getCurrentUser()
                )

        state = None
        if params.get('state'):
            try:
                state = Study.State(params['state'])
            except ValueError:
                raise RestException('Query parameter "state" may only be "active" or "complete".')

        return [
            {
                field: study[field]
                for field in
                Study.summaryFields
                }
            for study in
            Study.filterResultsByPermission(
                Study.find(query=None, annotator_user=annotator_user,
                           state=state, sort=sort),
                user=self.getCurrentUser(),
                level=AccessType.READ, limit=limit, offset=offset
            )
        ]


    @describeRoute(
        Description('Get a study by ID.')
        .param('id', 'The ID of the study.', paramType='path')
        .param('format', 'The output format.',
               paramType='query', required=False, enum=('csv', 'json'), default='json')
        .errorResponse()
    )
    @access.public
    @loadmodel(model='study', plugin='isic_archive', level=AccessType.READ)
    def getStudy(self, study, params):
        if params.get('format') == 'csv':
            cherrypy.response.stream = True
            cherrypy.response.headers['Content-Type'] = 'text/csv'
            cherrypy.response.headers['Content-Disposition'] = 'attachment; filename="%s"' % study['name']
            return functools.partial(self._getStudyCSVStream, study)

        else:
            output = self.model('study', 'isic_archive').filter(
                study, self.getCurrentUser())
            del output['_accessLevel']
            output['_modelType'] = 'study'
            output.update(study['meta'])
            return output

    def _getStudyCSVStream(self, study):
        featureset = self.model('featureset', 'isic_archive').load(study['meta']['featuresetId'])
        csv_fields = tuple(itertools.chain(
            ('study_name', 'study_id',
             'user_login_name', 'user_id',
             # TOOD: replace 'image_name' with 'isic_lesion_id'
             'image_name', 'image_id',
             'superpixel_id'),
            # (feature['id'] for feature in featureset['image_features']),
            (feature['id'] for feature in featureset['region_features'])
        ))

        response_body = StringIO()
        csv_writer = csv.DictWriter(response_body, csv_fields, restval='')

        csv_writer.writeheader()
        yield response_body.getvalue()
        response_body.seek(0)
        response_body.truncate()

        for annotator_user, image_item in itertools.product(
            self.model('study', 'isic_archive').getAnnotators(study).sort('login', pymongo.ASCENDING),
            self.model('study', 'isic_archive').getImages(study).sort('name', pymongo.ASCENDING)
        ):
            # this will iterate either 0 or 1 times
            for annotation in self.model('study', 'isic_archive').childAnnotations(
                study=study,
                annotator_user=annotator_user,
                image_item=image_item,
                state=self.model('study', 'isic_archive').State.COMPLETE
            ):
                # TODO: move this into the query
                if 'region_features' in annotation['meta']['annotations']:
                    superpixel_count = len(annotation['meta']['annotations']['region_features'].itervalues().next())
                    for superpixel_num in xrange(superpixel_count):

                        out_dict = {
                            'study_name': study['name'],
                            'study_id': str(study['_id']),
                            'user_login_name': annotator_user['login'],
                            'user_id': str(annotator_user['_id']),
                            'image_name': image_item['name'],
                            'image_id': str(image_item['_id']),
                            'superpixel_id': superpixel_num,
                        }
                        for feature_name, feature_value in annotation['meta']['annotations']['region_features'].iteritems():
                            out_dict[feature_name] = feature_value[superpixel_num]

                        csv_writer.writerow(out_dict)
                        yield response_body.getvalue()
                        response_body.seek(0)
                        response_body.truncate()


    @describeRoute(
        Description('Get the annotator users that comprise a study.')
        .param('id', 'The ID of the study.', paramType='path')
        .errorResponse('ID was invalid.')
    )
    @access.public
    @loadmodel(model='study', plugin='isic_archive', level=AccessType.READ)
    def getStudyUsers(self, study, params):
        summary_fields = ['_id', 'login']
        return [
            {field: user[field] for field in summary_fields}
            for user in
            self.model('study', 'isic_archive').getAnnotators(study).sort(
                'login', pymongo.ASCENDING)
            ]

    @describeRoute(
        Description('Get the segmentations that comprise a study.')
            .param('id', 'The ID of the study.', paramType='path')
            .errorResponse('ID was invalid.')
    )
    @access.public
    @loadmodel(model='study', plugin='isic_archive', level=AccessType.READ)
    def getStudySegmentations(self, study, params):
        summary_fields = ['_id']
        return [
            {field: image[field] for field in summary_fields}
            for image in
            # TODO: sort this output
            self.model('study', 'isic_archive').getSegmentations(study)
            ]

    @describeRoute(
        Description('Get the images (from segmentations) that comprise a study.')
        .param('id', 'The ID of the study.', paramType='path')
        .errorResponse('ID was invalid.')
    )
    @access.public
    @loadmodel(model='study', plugin='isic_archive', level=AccessType.READ)
    def getStudyImages(self, study, params):
        summary_fields = ['_id', 'name']
        return [
            {field: image[field] for field in summary_fields}
            for image in
            self.model('study', 'isic_archive').getImages(study).sort(
                'name', pymongo.ASCENDING)
            ]


    @describeRoute(
        Description('Redirect to an active annotation study task.')
        .param('id', 'The study to search for annotation tasks in.', paramType='path')
        .errorResponse()
    )
    @access.cookie
    @access.user
    @loadmodel(model='study', plugin='isic_archive', level=AccessType.READ)
    def redirectTask(self, study, params):
        # TODO: it's not strictly necessary to load the study

        # TODO: move this to model
        active_annotation_study = self.model('annotation', 'isic_archive').findOne({
            'baseParentId': ISIC.AnnotationStudies.collection['_id'],
            'meta.studyId': study['_id'],
            'meta.userId': self.getCurrentUser()['_id'],
            'meta.stopTime': None
        })

        if active_annotation_study:
            annotation_task_url = '/uda/map/%s' % active_annotation_study['_id']
            raise cherrypy.HTTPRedirect(annotation_task_url, status=307)
        else:
            raise RestException('No active annotations for this user in this study.')


    @describeRoute(
        Description('Create an annotation study.')
        .param('body', 'JSON containing the study parameters.', paramType='body')
        .errorResponse('Write access was denied on the parent folder.', 403)
    )
    @access.admin
    def createStudy(self, params):
        body_json = self.getBodyJson()

        self.requireParams(('name', 'annotatorIds', 'segmentationIds', 'featuresetId'), body_json)

        study_name = body_json['name']
        creator_user = self.getCurrentUser()
        annotator_users = [
            self.model('user').load(
                annotator_id, user=creator_user, level=AccessType.READ)
            for annotator_id in body_json['annotatorIds']
        ]
        segmentations = [
            self.model('segmentation', 'isic_archive').load(segmentation_id)
            for segmentation_id in body_json['segmentationIds']
        ]
        featureset = self.model('featureset', 'isic_archive').load(body_json['featuresetId'])

        self.model('study', 'isic_archive').createStudy(
            study_name, creator_user, featureset, annotator_users, segmentations)
