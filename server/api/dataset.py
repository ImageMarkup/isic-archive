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

import cherrypy

from girder.api import access
from girder.api.rest import Resource, loadmodel
from girder.api.describe import Description, describeRoute
from girder.constants import AccessType
from girder.models.model_base import AccessException, ValidationException


class DatasetResource(Resource):
    def __init__(self):
        super(DatasetResource, self).__init__()
        self.resourceName = 'dataset'

        self.route('GET', (), self.find)
        self.route('GET', (':id',), self.getDataset)
        self.route('POST', (), self.ingestDataset)

    @describeRoute(
        Description('Return a list of lesion image datasets.')
        .pagingParams(defaultSort='lowerName')
        .errorResponse()
    )
    @access.public
    def find(self, params):
        Dataset = self.model('dataset', 'isic_archive')

        limit, offset, sort = self.getPagingParameters(params, 'lowerName')

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

        if cherrypy.request.headers['Content-Type'] == 'application/json':
            params = self.getBodyJson()
        self.requireParams(('uploadFolderId', 'name'), params)

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
            uploadFolder=uploadFolder, user=user, name=name,
            description=description, license=licenseValue, signature=signature,
            anonymous=anonymous, attribution=attribution)
