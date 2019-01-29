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

import cherrypy

from girder.api import access
from girder.api.describe import autoDescribeRoute, describeRoute, Description
from girder.api.rest import loadmodel, RestException
from girder.constants import AccessType, SortDir, TokenScope
from girder.exceptions import AccessException, GirderException, ValidationException
from girder.models.file import File
from girder.utility import RequestBodyStream

from isic_archive_tasks.image import ingestImage
from isic_archive_tasks.zip import ingestBatchFromZipfile

from ..models.dataset import Dataset
from ..models.image import Image
from .base import IsicResource
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
        self.route('POST', (':id', 'zipBatch'), self.addZipBatch)
        self.route('POST', (':id', 'zip'), self.initiateZipUploadToS3)
        self.route('DELETE', (':id', 'zip', ':batchId'), self.cancelZipUploadToS3)
        self.route('POST', (':id', 'zip', ':batchId'), self.finalizeZipUploadToS3)
        self.route('GET', (':id', 'review'), self.getReviewImages)
        self.route('POST', (':id', 'review'), self.submitReviewImages)
        self.route('GET', (':id', 'metadata'), self.getRegisteredMetadata)
        self.route('POST', (':id', 'metadata'), self.registerMetadata)
        self.route('DELETE', (':id', 'metadata', ':metadataFileId'), self.removeMetadata)
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

    @autoDescribeRoute(
        Description('Set the access control list for a dataset.')
        .modelParam('id', description='The ID of the dataset.', paramType='path',
                    model='dataset', plugin='isic_archive', level=AccessType.ADMIN)
        .jsonParam('access', 'The JSON-encoded access control list.', paramType='form',
                   requireObject=True)
        .param('public', 'Whether the dataset should be publicly visible.', paramType='form',
               dataType='boolean')
        .errorResponse('ID was invalid.')
    )
    @access.user
    def setDatasetAccess(self, dataset, access, public, params):
        # Since this is often submitted as a URLEncoded form by upstream Girder's client widget,
        # the integer in the 'access' field is not decoded correctly by 'self._decodeParams'; so,
        # use autoDescribeRoute to decode fields

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

        ingestImage.delay(image['_id'])

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
        Description('Initiate a direct-to-S3 upload of a ZIP file of images.')
        .notes('This endpoint returns information that allows the client to upload a '
               'ZIP file of images directly to an Amazon Web Services (AWS) S3 bucket.'
               '\n\n'
               'It\'s recommended that the client use an AWS SDK, such as '
               '[Boto 3](https://github.com/boto/boto3) or '
               '[AWS SDK for JavaScript](https://github.com/aws/aws-sdk-js), '
               'to simplify authenticating and uploading the file.'
               '\n\n'
               'More specifically, this endpoint returns a JSON response that includes:\n'
               '- Temporary security credentials to authenticate with AWS:\n'
               '  - `accessKeyId`\n'
               '  - `secretAccessKey`\n'
               '  - `sessionToken`\n'
               '- An S3 bucket name and object key in which to upload the file:\n'
               '  - `bucketName`\n'
               '  - `objectKey`\n'
               '- A batch identifier for subsequent API calls:\n'
               '  - `batchId`\n'
               '\n\n'
               'After calling this endpoint, the client should use this information to upload '
               'the ZIP file directly to S3, as shown in the examples below.'
               '\n\n'
               '#### Example using Boto 3\n'
               '```\n'
               'import boto3\n'
               's3 = boto3.client(\n'
               '    \'s3\',\n'
               '    aws_access_key_id=response[\'accessKeyId\'],\n'
               '    aws_secret_access_key=response[\'secretAccessKey\'],\n'
               '    aws_session_token=response[\'sessionToken\']\n'
               ')\n'
               '\n'
               'with open(\'images.zip\', \'rb\') as data:\n'
               '    s3.upload_fileobj(\n'
               '        Fileobj=data,\n'
               '        Bucket=response[\'bucketName\'],\n'
               '        Key=response[\'objectKey\']\n'
               '    )\n'
               '\n'
               '# Store batch identifier\n'
               'batchId = response[\'batchId\']\n'
               '```\n\n'
               '#### Example using AWS SDK for JavaScript\n'
               '```\n'
               'AWS.config.update({\n'
               '    accessKeyId: response.accessKeyId,\n'
               '    secretAccessKey: response.secretAccessKey,\n'
               '    sessionToken: response.sessionToken\n'
               '});\n'
               '\n'
               '// Store batch identifier\n'
               'var batchId = response.batchId;\n'
               '\n'
               'var s3 = new AWS.S3({\n'
               '    apiVersion: \'2006-03-01\'\n'
               '});\n'
               '\n'
               'var params = {\n'
               '    Bucket: response.bucketName,\n'
               '    Key: response.objectKey,\n'
               '    Body: data\n'
               '};\n'
               's3.upload(params, function (err, data) {\n'
               '    if (err) {\n'
               '        console.log(\"Error\", err);\n'
               '    } else {\n'
               '        // Uploaded\n'
               '    }\n'
               '});\n'
               '```\n\n'
               '#### Finalizing the upload\n'
               '\n\n'
               'To finalize the upload, the client should call '
               '`POST /dataset/{id}/zip/{batchId}`.'
               '\n\n'
               'To cancel the upload, the client should call '
               '`DELETE /dataset/{id}/zip/{batchId}`.'
               )
        .param('id', 'The ID of the dataset.', paramType='path')
        .param('signature', 'Signature of license agreement.', paramType='form')
    )
    @access.user
    @loadmodel(model='dataset', plugin='isic_archive', level=AccessType.WRITE)
    def initiateZipUploadToS3(self, dataset, params):
        params = self._decodeParams(params)
        self.requireParams(['signature'], params)

        user = self.getCurrentUser()
        User().requireCreateDataset(user)

        signature = params['signature'].strip()
        if not signature:
            raise ValidationException('Signature must be specified.', 'signature')

        try:
            return Dataset().initiateZipUploadS3(dataset=dataset, signature=signature, user=user)
        except GirderException as e:
            raise RestException(e.message)

    @describeRoute(
        Description('Cancel a direct-to-S3 upload of a ZIP file of images.')
        .notes('Call this to cancel a direct-to-S3 upload instead of finalizing it.')
        .param('id', 'The ID of the dataset.', paramType='path')
        .param('batchId', 'The ID of the batch.', paramType='path')
    )
    @access.user
    @loadmodel(map={'batchId': 'batch'}, model='batch', plugin='isic_archive')
    @loadmodel(model='dataset', plugin='isic_archive', level=AccessType.WRITE)
    def cancelZipUploadToS3(self, dataset, batch, params):
        user = self.getCurrentUser()
        User().requireCreateDataset(user)

        try:
            Dataset().cancelZipUploadS3(dataset=dataset, batch=batch, user=user)
        except GirderException as e:
            raise RestException(e.message)

    @describeRoute(
        Description('Finalize a direct-to-S3 upload of a ZIP file of images.')
        .notes('Call this after uploading the ZIP file of images to S3. '
               'The images in the ZIP file will be added to the dataset.')
        .param('id', 'The ID of the dataset.', paramType='path')
        .param('batchId', 'The ID of the batch.', paramType='path')
    )
    @access.user
    @loadmodel(map={'batchId': 'batch'}, model='batch', plugin='isic_archive')
    @loadmodel(model='dataset', plugin='isic_archive', level=AccessType.WRITE)
    def finalizeZipUploadToS3(self, dataset, batch, params):
        user = self.getCurrentUser()
        # Note: we don't require the finalizer of the upload to be the creator of the batch
        User().requireCreateDataset(user)

        Dataset().finalizeZipUploadS3(batch)
        cherrypy.response.status = 201

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
        Description('Delete metadata registered with a dataset.')
        .param('id', 'The ID of the dataset.', paramType='path')
        .param('metadataFileId', 'The ID of the .csv metadata file.', paramType='path')
    )
    @access.admin
    # File is attached to dataset, so access level refers to permission on dataset
    @loadmodel(model='file', map={'metadataFileId': 'metadataFile'}, level=AccessType.SITE_ADMIN)
    @loadmodel(model='dataset', plugin='isic_archive', level=AccessType.SITE_ADMIN)
    def removeMetadata(self, dataset, metadataFile, params):
        self._requireMetadataFile(dataset, metadataFile)
        Dataset().removeMetadata(dataset=dataset, metadataFile=metadataFile)

        # No Content
        cherrypy.response.status = 204

    @describeRoute(
        Description('Download metadata registered with dataset.')
        .param('id', 'The ID of the dataset.', paramType='path')
        .param('metadataFileId', 'The ID of the .csv metadata file.', paramType='path')
    )
    @access.cookie
    @access.public(scope=TokenScope.DATA_READ)
    # File is attached to dataset, so access level refers to permission on dataset
    @loadmodel(model='file', map={'metadataFileId': 'metadataFile'}, level=AccessType.WRITE)
    @loadmodel(model='dataset', plugin='isic_archive', level=AccessType.WRITE)
    def downloadMetadata(self, dataset, metadataFile, params):
        user = self.getCurrentUser()
        User().requireReviewDataset(user)

        self._requireMetadataFile(dataset, metadataFile)
        return File().download(metadataFile)

    @describeRoute(
        Description('Apply registered metadata to a dataset.')
        .param('id', 'The ID of the dataset.', paramType='path')
        .param('metadataFileId', 'The ID of the .csv metadata file.', paramType='path')
        .param('save', 'Whether to save the metadata to the dataset if validation succeeds.',
               dataType='boolean', default=False, paramType='form')
    )
    @access.user
    # File is attached to dataset, so access level refers to permission on dataset
    @loadmodel(model='file', map={'metadataFileId': 'metadataFile'}, level=AccessType.ADMIN)
    @loadmodel(model='dataset', plugin='isic_archive', level=AccessType.ADMIN)
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

    def _requireMetadataFile(self, dataset, metadataFile):
        """Raise a ValidationException if the metadata file is not registered with the dataset."""
        if metadataFile is None or not any(registration['fileId'] == metadataFile['_id']
                                           for registration in dataset['metadataFiles']):
            raise ValidationException('Metadata file ID is not registered.', 'metadataFileId')
