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
import mimetypes

from girder.api import access
from girder.api.rest import RestException, loadmodel
from girder.api.describe import Description, describeRoute
from girder.constants import AccessType, SortDir, TokenScope
from girder.exceptions import AccessException, ValidationException
from girder.models.file import File
from girder.utility import RequestBodyStream

from .base import IsicResource
from ..models.dataset import Dataset
from ..models.image import Image
from ..models.user import User

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
        self.route('GET', (':id', 'access'), self.getDatasetAccess)
        self.route('PUT', (':id', 'access'), self.setDatasetAccess)
        self.route('POST', (), self.createDataset)
        self.route('POST', (':id', 'image'), self.addImage)
        self.route('POST', (':id', 'zip'), self.addZipBatch)
        self.route('GET', (':id', 'review'), self.getReviewImages)
        self.route('POST', (':id', 'review'), self.submitReviewImages)
        self.route('GET', (':id', 'metadata'), self.getRegisteredMetadata)
        self.route('POST', (':id', 'metadata'), self.registerMetadata)
        self.route('GET', (':id', 'metadata', ':metadataFileId', 'download'), self.downloadMetadata)
        self.route('POST', (':id', 'metadata', ':metadataFileId', 'apply'), self.applyMetadata)

    @describeRoute(
        Description('Return a list of lesion image datasets.')
        .pagingParams(defaultSort='name')
        .param('detail', 'Display the full information for each image, instead of a summary.',
               required=False, dataType='boolean', default=False)
        .errorResponse()
    )
    @access.cookie
    @access.public
    def find(self, params):
        user = self.getCurrentUser()
        detail = self.boolParam('detail', params, default=False)
        limit, offset, sort = self.getPagingParameters(params, 'name')

        filterFunc = Dataset().filter if detail else Dataset().filterSummary
        return [
            filterFunc(dataset, user)
            for dataset in
            Dataset().list(user=user, limit=limit, offset=offset, sort=sort)
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
        user = self.getCurrentUser()
        return Dataset().filter(dataset, user)

    @describeRoute(
        Description('Get the access control list for a dataset.')
        .param('id', 'The ID of the dataset.', paramType='path')
        .errorResponse('ID was invalid.')
    )
    @access.user
    @loadmodel(model='dataset', plugin='isic_archive', level=AccessType.ADMIN)
    def getDatasetAccess(self, dataset, params):
        return {
            'access': Dataset().getFullAccessList(dataset),
            'public': dataset['public']
        }

    @describeRoute(
        Description('Set the access control list for a dataset.')
        .param('id', 'The ID of the dataset.', paramType='path')
        .param('access', 'The JSON-encoded access control list.', paramType='form')
        .param('public', 'Whether the dataset should be publicly visible.', paramType='form')
        .errorResponse('ID was invalid.')
    )
    @access.user
    @loadmodel(model='dataset', plugin='isic_archive', level=AccessType.ADMIN)
    def setDatasetAccess(self, dataset, params):
        params = self._decodeParams(params)
        self.requireParams(['access', 'public'], params)
        access = params['access']
        public = self.boolParam('public', params)

        Dataset().setAccessList(dataset, access)
        Dataset().setPublic(dataset, public)

    @describeRoute(
        Description('Create a lesion image dataset.')
        .param('name', 'Name of the dataset.', paramType='form')
        .param('description', 'Description of the dataset.', paramType='form')
        .param('license', 'License of the dataset.', paramType='form')
        .param('attribution', 'Attribution of the dataset.', paramType='form')
        .param('owner', 'Owner of the dataset.', paramType='form')
    )
    @access.user
    def createDataset(self, params):
        params = self._decodeParams(params)
        self.requireParams(['name', 'description', 'license', 'attribution', 'owner'], params)

        user = self.getCurrentUser()
        User().requireCreateDataset(user)

        dataset = Dataset().createDataset(
            name=params['name'],
            description=params['description'],
            license=params['license'],
            attribution=params['attribution'],
            owner=params['owner'],
            creatorUser=user
        )

        return Dataset().filter(dataset, user)

    @describeRoute(
        Description('Upload an image to a dataset.')
        .notes('Send the image data in the request body, as shown in the examples below, '
               'and the parameters in the query string. '
               'Note that the examples ignore authentication and error handling.\n\n'
               'In the examples, `file` is a '
               '[File](https://developer.mozilla.org/en-US/docs/Web/API/File) object, '
               'for example from an [&lt;input type="file"&gt;]'
               '(https://developer.mozilla.org/en-US/docs/Web/HTML/Element/input/file) '
               'element or a drag and drop operation\'s [DataTransfer]'
               '(https://developer.mozilla.org/en-US/docs/Web/API/DataTransfer) object.\n\n'
               'Example using [XMLHttpRequest]'
               '(https://developer.mozilla.org/en-US/docs/Web/API/XMLHttpRequest):\n'
               '```\n'
               'var req = new XMLHttpRequest();\n'
               'req.open(\'POST\', url, true); // url includes parameters\n'
               'req.onload = function (event) {\n'
               '    // Uploaded\n'
               '};\n'
               'req.setRequestHeader(\'Content-Type\', \'image/jpeg\');\n'
               'req.send(file);\n'
               '```\n\n'
               'Example using [jQuery.ajax()](http://api.jquery.com/jquery.ajax/):\n'
               '```\n'
               '$.ajax({\n'
               '     url: url, // url includes parameters\n'
               '     method: \'POST\',\n'
               '     data: file,\n'
               '     contentType: \'image/jpeg\',\n'
               '     processData: false,\n'
               '}).done(function (resp) {\n'
               '    // Uploaded\n'
               '});\n'
               '```\n\n'
               'Example using [axios](https://github.com/axios/axios):\n'
               '```\n'
               'axios({\n'
               '    method: \'post\',\n'
               '    url: url,\n'
               '    params: {\n'
               '        filename: \'my_image.jpg\',\n'
               '        signature: \'my signature\',\n'
               '    },\n'
               '    data: file,\n'
               '    headers: {\n'
               '        \'Content-Type\': \'image/jpeg\',\n'
               '    }\n'
               '}).then(function (resp) {\n'
               '    // Uploaded\n'
               '});\n'
               '```\n\n'
               'Note that files uploaded in the request body are not supported by '
               '[OpenAPI 2.0](https://swagger.io/docs/specification/2-0/file-upload/), '
               'so it\'s currently not possible to use this endpoint from the Swagger UI '
               'interface.')
        # Note: OpenAPI 3.0 supports files uploaded in the request body, but Swagger GUI may not
        # properly display the file upload UI. See:
        # - https://swagger.io/docs/specification/describing-request-body/file-upload/
        # - https://github.com/swagger-api/swagger-ui/issues/3641
        .param('id', 'The ID of the dataset.', paramType='path')
        .param('filename', 'Image filename.', paramType='query')
        .param('signature', 'Signature of license agreement.', paramType='query')
    )
    @access.user
    @loadmodel(model='dataset', plugin='isic_archive', level=AccessType.WRITE)
    def addImage(self, dataset, params):
        params = self._decodeParams(params)
        self.requireParams(['filename', 'signature'], params)

        user = self.getCurrentUser()
        User().requireCreateDataset(user)

        filename = params['filename'].strip()
        if not filename:
            raise ValidationException('Filename must be specified.', 'filename')

        signature = params['signature'].strip()
        if not signature:
            raise ValidationException('Signature must be specified.', 'signature')

        imageDataStream = RequestBodyStream(cherrypy.request.body)
        imageDataSize = len(imageDataStream)

        if not imageDataSize:
            raise RestException('No data provided in request body.')

        image = Dataset().addImage(
            dataset=dataset,
            imageDataStream=imageDataStream,
            imageDataSize=imageDataSize,
            filename=filename,
            signature=signature,
            user=user)

        return Image().filter(image, user=user)

    @describeRoute(
        Description('Upload a batch of ZIP images to a dataset.')
        .param('id', 'The ID of the dataset.', paramType='path')
        .param('zipFileId', 'The ID of the .zip file of images.', paramType='form')
        .param('signature', 'Signature of license agreement.', paramType='form')
    )
    @access.user
    @loadmodel(model='dataset', plugin='isic_archive', level=AccessType.WRITE)
    def addZipBatch(self, dataset, params):
        params = self._decodeParams(params)
        self.requireParams(['zipFileId', 'signature'], params)

        user = self.getCurrentUser()
        User().requireCreateDataset(user)

        zipFileId = params['zipFileId']
        if not zipFileId:
            raise ValidationException('No file was uploaded.', 'zipFileId')
        zipFile = File().load(zipFileId, user=user, level=AccessType.WRITE, exc=False)
        if not zipFile:
            raise ValidationException('Invalid upload file ID.', 'zipFileId')
        if not self._checkFileFormat(zipFile, ZIP_FORMATS):
            raise ValidationException('File must be in .zip format.', 'zipFileId')

        signature = params['signature'].strip()
        if not signature:
            raise ValidationException('Signature must be specified.', 'owner')

        # TODO: make this return something
        Dataset().addZipBatch(
            dataset=dataset, zipFile=zipFile, signature=signature, user=user, sendMail=True)

    @describeRoute(
        Description('Get a list of images in this dataset to QC Review.')
        .param('id', 'The ID of the dataset.', paramType='path')
        .param('limit', 'Result set size limit.', default=50, required=False, dataType='int')
        .errorResponse('ID was invalid.')
    )
    @access.user
    @loadmodel(model='dataset', plugin='isic_archive', level=AccessType.WRITE)
    def getReviewImages(self, dataset, params):
        user = self.getCurrentUser()
        User().requireReviewDataset(user)

        prereviewFolder = Dataset().prereviewFolder(dataset)
        if not prereviewFolder:
            raise AccessException('There are no pending Pre-review images for this dataset.')

        limit = int(params.get('limit', 50))

        output = [
            {
                field: image[field]
                for field in
                ['_id', 'name', 'updated', 'description', 'meta']
            }
            for image in
            Image().find(
                {'folderId': prereviewFolder['_id']},
                limit=limit, sort=[('name', SortDir.ASCENDING)]
            )
        ]

        return output

    @describeRoute(
        Description('Do a QC Review of images within a dataset.')
        .param('id', 'The ID of the dataset.', paramType='path')
        .param('accepted', 'The IDs of accepted images, as a JSON array.', paramType='form')
        .param('flagged', 'The IDs of flagged images, as a JSON array.', paramType='form')
        .errorResponse('ID was invalid.')
    )
    @access.user
    @loadmodel(model='dataset', plugin='isic_archive', level=AccessType.WRITE)
    def submitReviewImages(self, dataset, params):
        user = self.getCurrentUser()
        User().requireReviewDataset(user)

        params = self._decodeParams(params)
        self.requireParams(['accepted', 'flagged'], params)
        # TODO: validate that parameters are lists of strings

        acceptedImages = [
            Image().load(imageId, user=user, level=AccessType.READ, exc=True)
            for imageId in params['accepted']
        ]
        flaggedImages = [
            Image().load(imageId, user=user, level=AccessType.READ, exc=True)
            for imageId in params['flagged']
        ]

        Dataset().reviewImages(dataset, acceptedImages, flaggedImages, user)

        # TODO: return value?
        return {'status': 'success'}

    @describeRoute(
        Description('Get registered metadata for a dataset.')
        .param('id', 'The ID of the dataset.', paramType='path')
    )
    @access.user
    @loadmodel(model='dataset', plugin='isic_archive', level=AccessType.WRITE)
    def getRegisteredMetadata(self, dataset, params):
        user = self.getCurrentUser()
        User().requireReviewDataset(user)

        output = []
        for registration in dataset['metadataFiles']:
            # TODO: "File().load" can use the "fields" argument and be expressed
            # as a comprehension, once the fix from upstream Girder is available
            metadataFile = File().load(registration['fileId'], force=True, exc=True)
            output.append({
                'file': {
                    '_id': metadataFile['_id'],
                    'name': metadataFile['name']
                },
                'user': User().filterSummary(
                    User().load(registration['userId'], force=True, exc=True),
                    user),
                'time': registration['time']
            })
        return output

    @describeRoute(
        Description('Register metadata with a dataset.')
        .notes('Send the CSV metadata data in the request body with '
               'the `Content-Type` header set to `text/csv`.')
        .param('id', 'The ID of the dataset.', paramType='path')
        .param('filename', 'The metadata filename.', paramType='query')
    )
    @access.user
    @loadmodel(model='dataset', plugin='isic_archive', level=AccessType.WRITE)
    def registerMetadata(self, dataset, params):
        params = self._decodeParams(params)
        self.requireParams(['filename'], params)
        user = self.getCurrentUser()

        filename = params['filename'].strip()
        if not filename:
            raise ValidationException('Filename must be specified.', 'filename')

        metadataDataStream = RequestBodyStream(cherrypy.request.body)
        if not len(metadataDataStream):
            raise RestException('No data provided in request body.')

        Dataset().registerMetadata(
            dataset=dataset, user=user, metadataDataStream=metadataDataStream, filename=filename,
            sendMail=True)
        # TODO: return value?
        return {'status': 'success'}

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
        Description('Download metadata registered with dataset.')
        .param('id', 'The ID of the dataset.', paramType='path')
        .param('metadataFileId', 'The ID of the .csv metadata file.', paramType='path')
    )
    @access.cookie
    @access.public(scope=TokenScope.DATA_READ)
    @loadmodel(model='file', map={'metadataFileId': 'metadataFile'}, force=True, exc=False)
    @loadmodel(model='dataset', plugin='isic_archive', level=AccessType.WRITE)
    def downloadMetadata(self, dataset, metadataFile, params):
        user = self.getCurrentUser()

        # Re-load file to check permissions and use custom error message
        if metadataFile is not None:
            metadataFile = File().load(
                metadataFile['_id'], user=user, level=AccessType.WRITE, exc=False)

        if not metadataFile:
            raise ValidationException('Invalid metadata file ID.', 'metadataFileId')

        return File().download(metadataFile)

    @describeRoute(
        Description('Apply registered metadata to a dataset.')
        .param('id', 'The ID of the dataset.', paramType='path')
        .param('metadataFileId', 'The ID of the .csv metadata file.', paramType='path')
        .param('save', 'Whether to save the metadata to the dataset if validation succeeds.',
               dataType='boolean', default=False, paramType='form')
    )
    @access.user
    @loadmodel(model='file', map={'metadataFileId': 'metadataFile'}, force=True)
    @loadmodel(model='dataset', plugin='isic_archive', level=AccessType.WRITE)
    def applyMetadata(self, dataset, metadataFile, params):
        params = self._decodeParams(params)
        self.requireParams('save', params)
        save = self.boolParam('save', params)

        errors, warnings = Dataset().applyMetadata(
            dataset=dataset, metadataFile=metadataFile, save=save)
        return {
            'errors': [{'description': description} for description in errors],
            'warnings': [{'description': description} for description in warnings]
        }
