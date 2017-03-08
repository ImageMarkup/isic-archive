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

import mimetypes

from girder.api import access
from girder.api.rest import loadmodel
from girder.api.describe import Description, describeRoute
from girder.constants import AccessType, SortDir
from girder.models.model_base import AccessException, ValidationException

from .base import IsicResource

CSV_FORMATS = [
    'text/csv',
    'application/vnd.ms-excel'
]

ZIP_FORMATS = [
    'multipart/x-zip',
    'application/zip',
    'application/zip-compressed',
    'application/x-zip-compressed',
]


class DatasetResource(IsicResource):
    def __init__(self):
        super(DatasetResource, self).__init__()
        self.resourceName = 'dataset'

        self.route('GET', (), self.find)
        self.route('GET', (':id',), self.getDataset)
        self.route('POST', (), self.ingestDataset)
        self.route('GET', (':id', 'review'), self.getReviewImages)
        self.route('POST', (':id', 'review'), self.submitReviewImages)
        self.route('GET', (':id', 'metadata'), self.getRegisteredMetadata)
        self.route('POST', (':id', 'metadata'), self.registerMetadata)
        self.route('POST', (':id', 'metadata', ':fileId'), self.applyMetadata)

    @describeRoute(
        Description('Return a list of lesion image datasets.')
        .pagingParams(defaultSort='name')
        .errorResponse()
    )
    @access.cookie
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
    @access.cookie
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
        .param('zipFileId', 'The ID of the .zip file of images.')
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
        File = self.model('file')
        User = self.model('user', 'isic_archive')

        params = self._decodeParams(params)
        self.requireParams(['zipFileId', 'name', 'owner'], params)

        user = self.getCurrentUser()
        User.requireCreateDataset(user)

        zipFileId = params.get('zipFileId')
        if not zipFileId:
            raise ValidationException(
                'No file was uploaded.', 'zipFileId')
        zipFile = File.load(
            zipFileId, user=user, level=AccessType.WRITE, exc=False)
        if not zipFile:
            raise ValidationException(
                'Invalid upload file ID.', 'zipFileId')
        if not self._checkFileFormat(zipFile, ZIP_FORMATS):
            print(zipFile)
            raise ValidationException(
                'File must be in .zip format.', 'zipFileId')

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
            zipFile=zipFile, user=user, name=name, owner=owner,
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

        params = self._decodeParams(params)
        self.requireParams(['accepted', 'flagged'], params)
        # TODO: validate that parameters are lists of strings

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

    @describeRoute(
        Description('Get registered metadata for a dataset.')
        .param('id', 'The ID of the dataset.', paramType='path')
    )
    @access.user
    @loadmodel(model='dataset', plugin='isic_archive', level=AccessType.READ)
    def getRegisteredMetadata(self, dataset, params):
        File = self.model('file')
        User = self.model('user', 'isic_archive')

        user = self.getCurrentUser()
        User.requireReviewDataset(user)

        output = []
        for registration in dataset['meta']['metadataFiles']:
            # TODO: "File.load" can use the "fields" argument and be expressed
            # as a comprehension, once the fix from upstream Girder is available
            metadataFile = File.load(
                registration['fileId'], force=True, exc=True)
            output.append({
                'file': {
                    '_id': metadataFile['_id'],
                    'name': metadataFile['name']
                },
                'user': User.filteredSummary(
                    User.load(registration['userId'], force=True, exc=True),
                    user),
                'time': registration['time']
            })
        return output

    @describeRoute(
        Description('Register metadata with a dataset.')
        .param('id', 'The ID of the dataset.', paramType='path')
        .param('metadataFileId', 'The ID of the .csv metadata file.')
    )
    @access.user
    @loadmodel(model='dataset', plugin='isic_archive', level=AccessType.READ)
    def registerMetadata(self, dataset, params):
        Dataset = self.model('dataset', 'isic_archive')
        File = self.model('file')
        User = self.model('user', 'isic_archive')

        params = self._decodeParams(params)
        self.requireParams(['metadataFileId'], params)

        user = self.getCurrentUser()
        User.requireCreateDataset(user)

        metadataFile = File.load(
            params['metadataFileId'], user=user, level=AccessType.READ,
            exc=False)
        if not metadataFile:
            raise ValidationException(
                'Invalid metadata file ID.', 'metadataFileId')
        if not self._checkFileFormat(metadataFile, CSV_FORMATS):
            raise ValidationException(
                'File must be in .csv format.', 'metadataFileId')

        return Dataset.registerMetadata(
            dataset=dataset, user=user, metadataFile=metadataFile,
            sendMail=True)

    def _checkFileFormat(self, file, formats):
        """
        Check whether a file is of an expected format.

        :param file: The file document.
        :param formats: A list of valid formats.
        :return: True if the file is of an expected format.
        """
        if file['mimeType'] in formats:
            return True
        if file['mimeType'] in ['application/octet-stream', None] and \
                mimetypes.guess_type(file['name'], strict=False)[0] in formats:
            return True
        return False

    @describeRoute(
        Description('Apply registered metadata to a dataset.')
        .param('id', 'The ID of the dataset.', paramType='path')
        .param('fileId', 'The ID of the .csv metadata file.', paramType='path')
        .param('save', 'Whether to save the metadata to the dataset if '
               'validation succeeds.', dataType='boolean', default=False,
               paramType='form')
    )
    @access.user
    @loadmodel(model='file', map={'fileId': 'metadataFile'}, force=True)
    @loadmodel(model='dataset', plugin='isic_archive', level=AccessType.READ)
    def applyMetadata(self, dataset, metadataFile, params):
        Dataset = self.model('dataset', 'isic_archive')
        User = self.model('user', 'isic_archive')

        params = self._decodeParams(params)
        self.requireParams('save', params)
        save = self.boolParam('save', params)

        user = self.getCurrentUser()
        User.requireCreateDataset(user)

        errors = Dataset.applyMetadata(
            dataset=dataset, metadataFile=metadataFile, save=save)
        return {
            'errors': [{'description': description} for description in errors]
        }
