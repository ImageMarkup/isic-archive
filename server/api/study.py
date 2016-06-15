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
from girder.models.model_base import AccessException, ValidationException

from ..provision_utility import ISIC


class StudyResource(Resource):
    def __init__(self,):
        super(StudyResource, self).__init__()
        self.resourceName = 'study'

        self.route('GET', (), self.find)
        self.route('GET', (':id',), self.getStudy)
        self.route('GET', (':id', 'task'), self.redirectTask)
        self.route('POST', (), self.createStudy)
        self.route('POST', (':id', 'user'), self.addAnnotator)


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
        Study = self.model('study', 'isic_archive')
        Featureset = self.model('featureset', 'isic_archive')
        Segmentation = self.model('segmentation', 'isic_archive')
        Image = self.model('image', 'isic_archive')

        if params.get('format') == 'csv':
            cherrypy.response.stream = True
            cherrypy.response.headers['Content-Type'] = 'text/csv'
            cherrypy.response.headers['Content-Disposition'] = 'attachment; filename="%s.csv"' % study['name']
            return functools.partial(self._getStudyCSVStream, study)

        else:
            output = Study.filter(study, self.getCurrentUser())
            del output['_accessLevel']
            output['_modelType'] = 'study'

            output['featureset'] = Featureset.load(
                id=study['meta']['featuresetId'],
                fields=Featureset.summaryFields
            )

            userSummaryFields = ('_id', 'login', 'firstName', 'lastName')
            output['users'] = [
                {field: user[field] for field in userSummaryFields}
                for user in
                Study.getAnnotators(study).sort('login', pymongo.ASCENDING)
            ]

            output['segmentations'] = [
                {
                    field: segmentation[field]
                    for field in Segmentation.summaryFields
                }
                for segmentation in
                Study.getSegmentations(study)
            ]

            images = Image.find(
                {'_id': {'$in': [
                    segmentation['imageId']
                    for segmentation in output['segmentations']
                ]}},
                fields=Image.summaryFields
            )
            images = {image['_id']: image for image in images}
            for segmentation in output['segmentations']:
                segmentation['image'] = images.pop(segmentation.pop('imageId'))

            output['segmentations'].sort(
                key=lambda segmentation: segmentation['image']['name'])

            return output

    def _getStudyCSVStream(self, study):
        Study = self.model('study', 'isic_archive')
        Featureset = self.model('featureset', 'isic_archive')
        Image = self.model('image', 'isic_archive')

        featureset = Featureset.load(study['meta']['featuresetId'])
        csv_fields = tuple(itertools.chain(
            ('study_name', 'study_id',
             'user_login_name', 'user_id',
             'segmentation_id',
             'image_name', 'image_id'),
            (feature['id'] for feature in featureset['image_features']),
            ('superpixel_id',),
            (feature['id'] for feature in featureset['region_features'])
        ))

        response_body = StringIO()
        csv_writer = csv.DictWriter(response_body, csv_fields, restval='')

        csv_writer.writeheader()
        yield response_body.getvalue()
        response_body.seek(0)
        response_body.truncate()

        segmentations = list(Study.getSegmentations(study))
        images = Image.find({'_id': {'$in': [
            segmentation['imageId'] for segmentation in segmentations]}})
        images = {image['_id']: image for image in images}
        for segmentation in segmentations:
            segmentation['image'] = images.pop(segmentation.pop('imageId'))
        segmentations.sort(
            key=lambda segmentation: segmentation['image']['name'])

        for annotator_user, segmentation in itertools.product(
            Study.getAnnotators(study).sort('login', pymongo.ASCENDING),
            segmentations
        ):
            # this will iterate either 0 or 1 times
            for annotation in Study.childAnnotations(
                study=study,
                annotator_user=annotator_user,
                segmentation=segmentation,
                state=Study.State.COMPLETE
            ):
                out_dict_base = {
                    'study_name': study['name'],
                    'study_id': str(study['_id']),
                    'user_login_name': annotator_user['login'],
                    'user_id': str(annotator_user['_id']),
                    'segmentation_id': str(segmentation['_id']),
                    'image_name': segmentation['image']['name'],
                    'image_id': str(segmentation['image']['_id'])
                }

                out_dict = out_dict_base.copy()
                for image_feature in featureset['image_features']:
                    if image_feature['id'] in annotation['meta']['annotations']:
                        out_dict[image_feature['id']] = annotation['meta']['annotations'][image_feature['id']]
                csv_writer.writerow(out_dict)
                yield response_body.getvalue()
                response_body.seek(0)
                response_body.truncate()

                # TODO: move this into the query
                if 'region_features' in annotation['meta']['annotations']:
                    superpixel_count = len(annotation['meta']['annotations']['region_features'].itervalues().next())
                    for superpixel_num in xrange(superpixel_count):

                        out_dict = out_dict_base.copy()
                        out_dict['superpixel_id'] = superpixel_num
                        for feature_name, feature_value in annotation['meta']['annotations']['region_features'].iteritems():
                            out_dict[feature_name] = feature_value[superpixel_num]

                        csv_writer.writerow(out_dict)
                        yield response_body.getvalue()
                        response_body.seek(0)
                        response_body.truncate()


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

    def _requireStudyCreator(self, user):
        """Require that user is a designated study creator or site admin."""
        studyCreatorsGroup = self.model('group').findOne({'name': 'Study Creators'})
        if not studyCreatorsGroup or studyCreatorsGroup['_id'] not in user['groups']:
            if not user.get('admin', False):
                raise AccessException(
                    'Only members of the Study Creators group can create studies.')

    @describeRoute(
        Description('Create an annotation study.')
        .param('name', 'The name of the study.')
        .param('featuresetId', 'The featureset ID of the study.')
        .param('userIds',
               'The annotators user IDs of the study, as a JSON array.')
        .param('segmentationIds',
               'The segmentation IDs of the study, as a JSON array.')
        .errorResponse('Write access was denied on the parent folder.', 403)
    )
    @access.user
    def createStudy(self, params):
        if cherrypy.request.headers['Content-Type'] == 'application/json':
            params = self.getBodyJson()
        self.requireParams(
            ('name', 'featuresetId', 'userIds', 'segmentationIds'),
            params)

        studyName = params['name'].strip()

        creatorUser = self.getCurrentUser()
        self._requireStudyCreator(creatorUser)

        featureset = self.model('featureset', 'isic_archive').load(
            params['featuresetId'])
        if not featureset:
            raise ValidationException('Invalid featureset ID.', 'featuresetId')

        annotatorUsers = [
            self.model('user').load(
                annotatorUserId, user=creatorUser, level=AccessType.READ)
            for annotatorUserId in params['userIds']
        ]

        segmentations = [
            self.model('segmentation', 'isic_archive').load(segmentationId)
            for segmentationId in params['segmentationIds']
        ]

        study = self.model('study', 'isic_archive').createStudy(
            studyName, creatorUser, featureset, annotatorUsers, segmentations)

        # TODO return nothing? return full study? return 201 + Location header?
        return study

    @describeRoute(
        Description('Add a user as an annotator of a study.')
        .param('id', 'The ID of the study.', paramType='path')
        .param('userId', 'The ID of the user.')
        .errorResponse('ID was invalid.')
        .errorResponse('You don\'t have permission to add a study annotator.',
                       403)
    )
    @access.user
    @loadmodel(model='study', plugin='isic_archive', level=AccessType.WRITE)
    def addAnnotator(self, study, params):
        if cherrypy.request.headers['Content-Type'] == 'application/json':
            params = self.getBodyJson()
        self.requireParams('userId', params)

        creatorUser = self.getCurrentUser()

        annotatorUser = self.model('user').load(
            id=params['userId'], force=True)

        self.model('study', 'isic_archive').addAnnotator(
            study, annotatorUser, creatorUser)
        # TODO: return?
