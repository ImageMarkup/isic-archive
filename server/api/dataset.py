#!/usr/bin/env python
# -*- coding: utf-8 -*-

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
        self.route('POST', (), self.createDataset)


    @describeRoute(
        Description('Return a list of lesion image datasets.')
        .pagingParams(defaultSort='lowerName')
        .errorResponse()
    )
    @access.public
    def find(self, params):
        limit, offset, sort = self.getPagingParameters(params, 'lowerName')

        return [
            {
                field: dataset[field]
                for field in
                self.model('dataset', 'isic_archive').summaryFields
            }
            for dataset in
            self.model('dataset', 'isic_archive').list(
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
        return self.model('dataset', 'isic_archive').filter(
            dataset, self.getCurrentUser())

    @describeRoute(
        Description('Create a lesion image dataset.')
        .param('uploadFolderId', 'The ID of the folder that contains images '
               'and metadata.')
        .param('name', 'Name of the dataset.')
        .param('description', 'Description of the dataset.', required=False)
        .param('license', 'License of the dataset.', required=False)
        .param('signature', 'Signature of license agreement.', required=True)
        .param('anonymous', 'Whether to use an anonymous attribution for the '
               'dataset', dataType='boolean', required=False)
        .param('attribution', 'Attribution of the dataset.', required=False)
    )
    @access.user
    def createDataset(self, params):
        self.requireParams(('uploadFolderId', 'name'), params)

        # Require that user be a member of the Dataset Contributors group
        user = self.getCurrentUser()
        contributorsGroup = self.model('group').findOne({'name': 'Dataset Contributors'})
        if not contributorsGroup or contributorsGroup['_id'] not in user['groups']:
            raise AccessException(
                'Only dataset contributors can create datasets.')

        uploadFolderId = params.get('uploadFolderId', None)
        if not uploadFolderId:
            raise ValidationException(
                'No files were uploaded.', 'uploadFolderId')
        uploadFolder = self.model('folder').load(
            uploadFolderId, user=user, level=AccessType.WRITE)
        if not uploadFolder:
            raise ValidationException(
                'Invalid upload folder ID.', 'uploadFolderId')

        name = params['name'].strip()
        description = params.get('description', '').strip()
        license = params.get('license', '').strip()

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

        return self.model('dataset', 'isic_archive').ingestDataset(
            uploadFolder=uploadFolder, user=user, name=name,
            description=description, license=license, signature=signature,
            anonymous=anonymous, attribution=attribution)
