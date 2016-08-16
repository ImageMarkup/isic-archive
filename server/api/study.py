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

import csv
from cStringIO import StringIO
import functools
import itertools
import json

import cherrypy

from girder.api import access
from girder.api.rest import Resource, RestException, loadmodel
from girder.api.describe import Description, describeRoute
from girder.constants import AccessType, SortDir
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
        .pagingParams(defaultSort='lowerName')
        .param('state', 'Filter studies to those at a given state',
               paramType='query', required=False, enum=('active', 'complete'))
        .param('userId',
               'Filter studies to those containing a user ID, or "me".',
               paramType='query', required=False)
        .errorResponse()
    )
    @access.public
    def find(self, params):
        Study = self.model('study', 'isic_archive')

        limit, offset, sort = self.getPagingParameters(params, 'lowerName')

        annotatorUser = None
        if params.get('userId'):
            if params['userId'] == 'me':
                annotatorUser = self.getCurrentUser()
            else:
                annotatorUser = self.model('user').load(
                    id=params['userId'],
                    level=AccessType.READ,
                    user=self.getCurrentUser()
                )

        state = None
        if params.get('state'):
            try:
                state = Study.State(params['state'])
            except ValueError:
                raise RestException('Query parameter "state" may only '
                                    'be "active" or "complete".')

        return [
            {
                field: study[field]
                for field in
                Study.summaryFields
            }
            for study in
            Study.filterResultsByPermission(
                Study.find(query=None, annotatorUser=annotatorUser,
                           state=state, sort=sort),
                user=self.getCurrentUser(),
                level=AccessType.READ, limit=limit, offset=offset
            )
        ]

    @describeRoute(
        Description('Get a study by ID.')
        .param('id', 'The ID of the study.', paramType='path')
        .param('format', 'The output format.',
               paramType='query', required=False, enum=('csv', 'json'),
               default='json')
        .errorResponse()
    )
    @access.public
    @loadmodel(model='study', plugin='isic_archive', level=AccessType.READ)
    def getStudy(self, study, params):
        Study = self.model('study', 'isic_archive')
        Featureset = self.model('featureset', 'isic_archive')
        Segmentation = self.model('segmentation', 'isic_archive')
        Image = self.model('image', 'isic_archive')
        User = self.model('user')

        if params.get('format') == 'csv':
            cherrypy.response.stream = True
            cherrypy.response.headers['Content-Type'] = 'text/csv'
            cherrypy.response.headers['Content-Disposition'] = \
                'attachment; filename="%s.csv"' % study['name']
            return functools.partial(self._getStudyCSVStream, study)

        else:
            output = Study.filter(study, self.getCurrentUser())
            del output['_accessLevel']
            output['_modelType'] = 'study'

            output['featureset'] = Featureset.load(
                id=study['meta']['featuresetId'],
                fields=Featureset.summaryFields
            )

            userSummaryFields = ['_id', 'login', 'firstName', 'lastName']

            output['creator'] = User.load(
                output.pop('creatorId'),
                force=True, exc=True,
                fields=userSummaryFields)

            output['users'] = [
                {
                    field: user[field]
                    for field in
                    userSummaryFields
                }
                for user in
                Study.getAnnotators(study).sort('login', SortDir.ASCENDING)
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
        csvFields = tuple(itertools.chain(
            ('study_name', 'study_id',
             'user_login_name', 'user_id',
             'segmentation_id',
             'image_name', 'image_id',
             'flag_status', 'elapsed_seconds'),
            (feature['id'] for feature in featureset['image_features']),
            ('superpixel_id',),
            (feature['id'] for feature in featureset['region_features'])
        ))

        responseBody = StringIO()
        csvWriter = csv.DictWriter(responseBody, csvFields, restval='')

        csvWriter.writeheader()
        yield responseBody.getvalue()
        responseBody.seek(0)
        responseBody.truncate()

        segmentations = list(Study.getSegmentations(study))
        images = Image.find({'_id': {'$in': [
            segmentation['imageId'] for segmentation in segmentations]}})
        images = {image['_id']: image for image in images}
        for segmentation in segmentations:
            segmentation['image'] = images.pop(segmentation.pop('imageId'))
        segmentations.sort(
            key=lambda segmentation: segmentation['image']['name'])

        for annotatorUser, segmentation in itertools.product(
            Study.getAnnotators(study).sort('login', SortDir.ASCENDING),
            segmentations
        ):
            # this will iterate either 0 or 1 times
            for annotation in Study.childAnnotations(
                study=study,
                annotatorUser=annotatorUser,
                segmentation=segmentation,
                state=Study.State.COMPLETE
            ):
                elapsedSeconds = \
                    int((annotation['meta']['stopTime'] -
                         annotation['meta']['startTime']).total_seconds())

                outDictBase = {
                    'study_name': study['name'],
                    'study_id': str(study['_id']),
                    'user_login_name': annotatorUser['login'],
                    'user_id': str(annotatorUser['_id']),
                    'segmentation_id': str(segmentation['_id']),
                    'image_name': segmentation['image']['name'],
                    'image_id': str(segmentation['image']['_id']),
                    'flag_status': annotation['meta']['status'],
                    'elapsed_seconds': elapsedSeconds
                }

                outDict = outDictBase.copy()
                for imageFeature in featureset['image_features']:
                    if imageFeature['id'] in annotation['meta']['annotations']:
                        outDict[imageFeature['id']] = \
                            annotation['meta']['annotations'][imageFeature['id']]  # noqa: E501
                csvWriter.writerow(outDict)
                yield responseBody.getvalue()
                responseBody.seek(0)
                responseBody.truncate()

                # TODO: move this into the query
                if 'region_features' in annotation['meta']['annotations']:
                    superpixelCount = len(
                        annotation['meta']['annotations']['region_features'].itervalues().next())  # noqa: E501
                    for superpixelMum in xrange(superpixelCount):

                        outDict = outDictBase.copy()
                        outDict['superpixel_id'] = superpixelMum
                        for featureName, featureValue in \
                                annotation['meta']['annotations']['region_features'].iteritems():  # noqa: E501
                            outDict[featureName] = featureValue[superpixelMum]

                        csvWriter.writerow(outDict)
                        yield responseBody.getvalue()
                        responseBody.seek(0)
                        responseBody.truncate()

    @describeRoute(
        Description('Redirect to an active annotation study task.')
        .param('id', 'The study to search for annotation tasks in.',
               paramType='path')
        .errorResponse()
    )
    @access.cookie
    @access.user
    @loadmodel(model='study', plugin='isic_archive', level=AccessType.READ)
    def redirectTask(self, study, params):
        Annotation = self.model('annotation', 'isic_archive')
        # TODO: it's not strictly necessary to load the study

        # TODO: move this to model
        activeAnnotationStudy = Annotation.findOne({
            'baseParentId': ISIC.AnnotationStudies.collection['_id'],
            'meta.studyId': study['_id'],
            'meta.userId': self.getCurrentUser()['_id'],
            'meta.stopTime': None
        })

        if activeAnnotationStudy:
            annotationTaskUrl = '/uda/map/%s' % activeAnnotationStudy['_id']
            raise cherrypy.HTTPRedirect(annotationTaskUrl, status=307)
        else:
            raise RestException(
                'No active annotations for this user in this study.')

    def _requireStudyAdmin(self, user):
        """Require that user is a designated study admin or site admin."""
        studyAdminsGroup = self.model('group').findOne({
            'name': 'Study Administrators'})
        if not studyAdminsGroup or \
                studyAdminsGroup['_id'] not in user['groups']:
            if not user.get('admin', False):
                raise AccessException('Only members of the Study Administrators'
                                      ' group can create or modify studies.')

    @describeRoute(
        Description('Create an annotation study.')
        .param('name', 'The name of the study.', paramType='form')
        .param('featuresetId', 'The featureset ID of the study.',
               paramType='form')
        .param('userIds',
               'The annotators user IDs of the study, as a JSON array.',
               paramType='form')
        .param('segmentationIds',
               'The segmentation IDs of the study, as a JSON array.',
               paramType='form')
        .errorResponse('Write access was denied on the parent folder.', 403)
    )
    @access.user
    def createStudy(self, params):
        isJson = cherrypy.request.headers['Content-Type'] == 'application/json'
        if isJson:
            params = self.getBodyJson()
        self.requireParams(
            ('name', 'featuresetId', 'userIds', 'segmentationIds'),
            params)

        if not isJson:
            try:
                params['userIds'] = json.loads(params['userIds'])
            except ValueError:
                raise RestException('Invalid JSON passed in userIds parameter.')
            try:
                params['segmentationIds'] = json.loads(
                    params['segmentationIds'])
            except ValueError:
                raise RestException(
                    'Invalid JSON passed in segmentationIds parameter.')

        studyName = params['name'].strip()
        if not studyName:
            raise ValidationException('Name must not be empty.', 'name')

        creatorUser = self.getCurrentUser()
        self._requireStudyAdmin(creatorUser)

        featuresetId = params['featuresetId']
        if not featuresetId:
            raise ValidationException('Invalid featureset ID.', 'featuresetId')
        featureset = self.model('featureset', 'isic_archive').load(featuresetId)
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
        .param('userId', 'The ID of the user.', paramType='form')
        .errorResponse('ID was invalid.')
        .errorResponse('You don\'t have permission to add a study annotator.',
                       403)
    )
    @access.user
    @loadmodel(model='study', plugin='isic_archive', level=AccessType.READ)
    def addAnnotator(self, study, params):
        # TODO: make the loadmodel decorator use AccessType.WRITE,
        # once permissions work
        if cherrypy.request.headers['Content-Type'] == 'application/json':
            params = self.getBodyJson()
        self.requireParams('userId', params)

        creatorUser = self.getCurrentUser()
        self._requireStudyAdmin(creatorUser)

        annotatorUser = self.model('user').load(
            id=params['userId'], force=True)

        self.model('study', 'isic_archive').addAnnotator(
            study, annotatorUser, creatorUser)
        # TODO: return?
