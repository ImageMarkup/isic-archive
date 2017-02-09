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

import json

import cherrypy

from girder.api import access
from girder.api.rest import Resource, loadmodel, RestException
from girder.api.describe import Description, describeRoute
from girder.constants import AccessType, SortDir
from girder.models.model_base import AccessException, ValidationException


class DatasetResource(Resource):
    def __init__(self):
        super(DatasetResource, self).__init__()
        self.resourceName = 'dataset'

        self.route('GET', (), self.find)
        self.route('GET', (':id',), self.getDataset)
        self.route('POST', (), self.ingestDataset)
        self.route('GET', (':id', 'review'), self.getReviewImages)
        self.route('POST', (':id', 'review'), self.submitReviewImages)

    @describeRoute(
        Description('Return a list of lesion image datasets.')
        .pagingParams(defaultSort='name')
        .errorResponse()
    )
    @access.public
    def find(self, params):
        Dataset = self.model('dataset', 'isic_archive')

        limit, offset, sort = self.getPagingParameters(params, 'name')

        return [
            {
                field: dataset[field]
                for field in
                Dataset.summaryFields
            }
            for dataset in
            Dataset.list(
                user=self.getCurrentUser(),
                limit=limit, offset=offset, sort=sort)
        ]

    @describeRoute(
        Description('Return a lesion image dataset\'s details.')
        .param('id', 'The ID of the dataset.', paramType='path')
        .errorResponse('ID was invalid.')
    )
    @access.public
    @loadmodel(model='dataset', plugin='isic_archive', level=AccessType.READ)
    def getDataset(self, dataset, params):
        Dataset = self.model('dataset', 'isic_archive')
        User = self.model('user', 'isic_archive')

        output = Dataset.filter(
            dataset, self.getCurrentUser())
        del output['_accessLevel']
        output['_modelType'] = 'dataset'
        output.update(dataset.get('meta', {}))

        output['creator'] = User.filteredSummary(
            User.load(
                output.pop('creatorId'),
                force=True, exc=True),
            self.getCurrentUser())

        return output

    @describeRoute(
        Description('Create a lesion image dataset.')
        .param('uploadFolderId', 'The ID of the folder that contains images '
               'and metadata.')
        .param('name', 'Name of the dataset.')
        .param('owner', 'Owner of the dataset.')
        .param('description', 'Description of the dataset.', required=False,
               paramType='form')
        .param('license', 'License of the dataset.', required=False,
               paramType='form')
        .param('signature', 'Signature of license agreement.', required=True,
               paramType='form')
        .param('anonymous', 'Whether to use an anonymous attribution for the '
               'dataset', dataType='boolean', required=False, paramType='form')
        .param('attribution', 'Attribution of the dataset.', required=False,
               paramType='form')
    )
    @access.user
    def ingestDataset(self, params):
        Dataset = self.model('dataset', 'isic_archive')
        Folder = self.model('folder')
        User = self.model('user', 'isic_archive')

        if cherrypy.request.headers['Content-Type'].split(';')[0] == \
                'application/json':
            params = self.getBodyJson()
        self.requireParams(('uploadFolderId', 'name', 'owner'), params)

        user = self.getCurrentUser()
        User.requireCreateDataset(user)

        uploadFolderId = params.get('uploadFolderId', None)
        if not uploadFolderId:
            raise ValidationException(
                'No files were uploaded.', 'uploadFolderId')
        uploadFolder = Folder.load(
            uploadFolderId, user=user, level=AccessType.WRITE, exc=False)
        if not uploadFolder:
            raise ValidationException(
                'Invalid upload folder ID.', 'uploadFolderId')

        name = params['name'].strip()
        owner = params['owner'].strip()
        if not owner:
            raise ValidationException(
                'Owner must be specified.', 'owner')
        description = params.get('description', '').strip()
        licenseValue = params.get('license', '').strip()

        # Enforce valid licensing metadata only at API level
        signature = params.get('signature', '').strip()
        if not signature:
            raise ValidationException(
                'Signature must be specified.', 'signature')
        anonymous = self.boolParam('anonymous', params, False)
        attribution = params.get('attribution', '').strip()
        if not anonymous and not attribution:
            raise ValidationException(
                'Attribution must be specified when not contributing '
                'anonymously.', 'attribution')

        # TODO: make this return only the dataset fields
        return Dataset.ingestDataset(
            uploadFolder=uploadFolder, user=user, name=name, owner=owner,
            description=description, license=licenseValue, signature=signature,
            anonymous=anonymous, attribution=attribution, sendMail=True)

    @describeRoute(
        Description('Get a list of images in this dataset to QC Review.')
        .param('id', 'The ID of the dataset.', paramType='path')
        .param('limit', 'Result set size limit.',
               default=50, required=False, dataType='int')
        .errorResponse('ID was invalid.')
    )
    @access.user
    @loadmodel(model='dataset', plugin='isic_archive', level=AccessType.READ)
    def getReviewImages(self, dataset, params):
        Dataset = self.model('dataset', 'isic_archive')
        Folder = self.model('folder')
        Image = self.model('image', 'isic_archive')
        User = self.model('user', 'isic_archive')

        user = self.getCurrentUser()
        User.requireReviewDataset(user)

        prereviewFolder = Dataset.prereviewFolder(dataset)
        if not (prereviewFolder and Folder.hasAccess(
                prereviewFolder, user=user, level=AccessType.READ)):
            raise AccessException(
                'User does not have access to any Pre-review images for this '
                'dataset.')

        limit = int(params.get('limit', 50))

        output = [
            {
                field: image[field]
                for field in
                Image.summaryFields + ['description', 'meta']
            }
            for image in
            Image.find(
                {'folderId': prereviewFolder['_id']},
                limit=limit, sort=[('name', SortDir.ASCENDING)]
            )
        ]

        return output

    @describeRoute(
        Description('Do a QC Review of images within a dataset.')
        .param('id', 'The ID of the dataset.', paramType='path')
        .param('accepted', 'The IDs of accepted images, as a JSON array.',
               paramType='form')
        .param('flagged', 'The IDs of flagged images, as a JSON array.',
               paramType='form')
        .errorResponse('ID was invalid.')
    )
    @access.user
    @loadmodel(model='dataset', plugin='isic_archive', level=AccessType.READ)
    def submitReviewImages(self, dataset, params):
        Dataset = self.model('dataset', 'isic_archive')
        Image = self.model('image', 'isic_archive')
        User = self.model('user', 'isic_archive')

        user = self.getCurrentUser()
        User.requireReviewDataset(user)

        isJson = cherrypy.request.headers['Content-Type'].split(';')[0] == \
            'application/json'
        if isJson:
            params = self.getBodyJson()
        self.requireParams(['accepted', 'flagged'], params)

        if not isJson:
            for field in ['accepted', 'flagged']:
                try:
                    params[field] = json.loads(params[field])
                except ValueError:
                    raise RestException(
                        'Invalid JSON passed in %s parameter.' % field)

        acceptedImages = [
            Image.load(imageId, user=user, level=AccessType.READ, exc=True)
            for imageId in params['accepted']
        ]
        flaggedImages = [
            Image.load(imageId, user=user, level=AccessType.READ, exc=True)
            for imageId in params['flagged']
        ]

        Dataset.reviewImages(dataset, acceptedImages, flaggedImages, user)

        # TODO: return value?
        return {'status': 'success'}
