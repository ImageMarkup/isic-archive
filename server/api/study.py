#!/usr/bin/env python
# -*- coding: utf-8 -*-

import cherrypy

from girder.api import access
from girder.api.rest import Resource, RestException, loadmodel
from girder.api.describe import Description
from girder.constants import AccessType

from ..provision_utility import ISIC


class StudyResource(Resource):
    def __init__(self,):
        self.resourceName = 'study'

        self.route('GET', (), self.find)
        self.route('GET', (':study_id', 'task'), self.redirectTask)
        self.route('POST', (), self.createStudy)


    @access.public
    def find(self, params):
        filters = dict()

        if params.get('user'):
            if params['user'] == 'me':
                filters['annotator_user'] = self.getCurrentUser()
            else:
                filters['annotator_user'] = self.model('user').load(
                    id=params['user'],
                    level=AccessType.READ,
                    user=self.getCurrentUser()
                )

        if params.get('state'):
            try:
                filters['state'] = self.model('study', 'isic_archive').State(params['state'])
            except ValueError:
                raise RestException('Query parameter "state" may only be "active" or "complete".')

        return [self.model('study', 'isic_archive').filter(study_folder)
                for study_folder in self.model('study', 'isic_archive').find(**filters)]

    find.description = (
        Description('Return a list of annotation studies.')
        .param('state', 'Filter studies to those at a given state',
               paramType='query', required=False, enum=('active', 'complete'))
        .param('user', 'Filter studies to those containing a user ID, or "me".',
               paramType='query', required=False)
        .errorResponse())


    @access.user
    @loadmodel(model='folder', map={'study_id': 'study_folder'}, level=AccessType.READ)
    def redirectTask(self, study_folder, params):
        # TODO: it's not strictly necessary to load the study

        # TODO: move this to model
        active_annotation_study = self.model('annotation', 'isic_archive').findOne({
            'baseParentId': ISIC.AnnotationStudies.collection['_id'],
            'meta.studyId': study_folder['_id'],
            'meta.userId': self.getCurrentUser()['_id'],
            'meta.stopTime': None
        })

        if active_annotation_study:
            annotation_task_url = '/uda/map/%s' % active_annotation_study['_id']
            raise cherrypy.HTTPRedirect(annotation_task_url, status=307)
        else:
            raise RestException('No active annotations for this user in this study.')

    redirectTask.cookieAuth = True
    redirectTask.description = (
        Description('Redirect to an active annotation study task.')
        .param('study_id', 'The study to search for annotation tasks in.',
               paramType='path', required=True)
        .errorResponse())


    @access.admin
    def createStudy(self, params):
        body_json = self.getBodyJson()

        self.requireParams(('name', 'annotatorIds', 'imageIds', 'featuresetId'), body_json)

        study_name = body_json['name']
        creator_user = self.getCurrentUser()
        annotator_users = [self.model('user').load(annotator_id, user=creator_user, level=AccessType.READ)
                           for annotator_id in body_json['annotatorIds']]
        # TODO: validate that these items are actually in the correct folder
        image_items = [self.model('item').load(image_id, user=creator_user, level=AccessType.READ)
                       for image_id in body_json['imageIds']]
        featureset = self.model('featureset', 'isic_archive').load(body_json['featuresetId'])

        self.model('study', 'isic_archive').createStudy(
            study_name, creator_user, featureset, annotator_users, image_items)


    createStudy.description = (
        Description('Create an annotation study.')
        .param('body', 'JSON containing the study parameters.', paramType='body')
        .errorResponse()
        .errorResponse('Write access was denied on the parent folder.', 403))
