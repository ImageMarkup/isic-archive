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
import json
import mimetypes

from girder.api import access
from girder.api.rest import RestException, loadmodel
from girder.api.describe import Description, describeRoute
from girder.constants import AccessType, SortDir
from girder.exceptions import AccessException, ValidationException
from girder.models.assetstore import Assetstore
from girder.models.file import File
from girder.models.setting import Setting
from girder.models.upload import Upload
from girder.utility import RequestBodyStream

from .base import IsicResource
from ..models.dataset import Dataset
from ..models.image import Image
from ..models.user import User
from ..settings import PluginSettings

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
        self.route('POST', (':id', 'imageZip'), self.addImageZip)
        self.route('POST', (':id', 'zip'), self.initZipUpload)
        self.route('POST', (':id', 'zip', ':zipUploadId', 'part'), self.addZipUploadPart)
        self.route('POST', (':id', 'zip', ':zipUploadId', 'completion'), self.finalizeZipUpload)
        self.route('DELETE', (':id', 'zip', ':zipUploadId'), self.cancelZipUpload)
        self.route('GET', (':id', 'review'), self.getReviewImages)
        self.route('POST', (':id', 'review'), self.submitReviewImages)
        self.route('GET', (':id', 'metadata'), self.getRegisteredMetadata)
        self.route('POST', (':id', 'metadata'), self.registerMetadata)
        self.route('POST', (':id', 'metadata', ':fileId'), self.applyMetadata)

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
        Description('Add images from a ZIP file to a dataset.')
        .param('id', 'The ID of the dataset.', paramType='path')
        .param('zipFileId', 'The ID of the .zip file of images.', paramType='form')
        .param('signature', 'Signature of license agreement.', paramType='form')
    )
    @access.user
    @loadmodel(model='dataset', plugin='isic_archive', level=AccessType.WRITE)
    def addImageZip(self, dataset, params):
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
        Description('Start a new direct-to-S3 upload of a ZIP file of images.')
        .notes('This endpoint returns information for the client to make a subsequent HTTP '
               'request to S3 either to upload the file--if the file is less than 32 MB in '
               'size--or to initiate a multi-part upload. For details on the S3 upload '
               'workflow, see the AWS S3 documentation: '
               'https://docs.aws.amazon.com/AmazonS3/latest/dev/UploadingObjects.html'
               '\n\n'
               'More specifically, this endpoint returns a JSON response in which the '
               '`_id` field contains the ZIP file upload ID to use in subsequent requests '
               'and in which the `s3` field contains the S3 request information. The client '
               'should use the value of `s3.chunked` (boolean) to determine which upload '
               'method to use.'
               '\n\n'
               '#### Single-part upload\n'
               'When `s3.chunked` is false, the client should make an HTTP request with the '
               'following properties to upload the file:\n\n'
               '|             |                                                     |\n'
               '|-------------|-----------------------------------------------------|\n'
               '| **Method**  | `s3.request.method`                                 |\n'
               '| **URL**     | `s3.request.url`                                    |\n'
               '| **Headers** | One for each key-value pair in `s3.request.headers` |\n'
               '|             | `Content-Length`: &lt;file size, in bytes&gt;       |\n'
               '|             | `Content-MD5`: base64-encoded MD5 digest of data    |\n'
               '| **Data**    | File content                                        |\n'
               '|             |                                                     |\n'
               '\n\n'
               'This S3 request is documented at '
               'https://docs.aws.amazon.com/AmazonS3/latest/dev/UploadObjSingleOpREST.html.'
               '\n\n'
               'To finalize the upload, the client should call '
               '`POST /dataset/{id}/zip/{zipUploadId}/completion`.'
               '\n\n'
               '#### Multi-part upload\n'
               'When `s3.chunked` is true, `s3.chunkLength` contains the size of each part '
               'to be uploaded, and the client should make an HTTP request with the following '
               'properties to initiate the multi-part upload:\n\n'
               '|             |                                                     |\n'
               '|-------------|-----------------------------------------------------|\n'
               '| **Method**  | `s3.request.method`                                 |\n'
               '| **URL**     | `s3.request.url`                                    |\n'
               '| **Headers** | One for each key-value pair in `s3.request.headers` |\n'
               '|             |                                                     |\n'
               '\n\n'
               'This request returns an XML document. The client should parse the XML to '
               'get the multi-part upload ID. The XPath expression for the ID is '
               '`/InitiateMultipartUploadResult/UploadId`.'
               '\n\n'
               'This S3 request is documented at '
               'https://docs.aws.amazon.com/AmazonS3/latest/API/mpUploadInitiate.html.'
               '\n\n'
               'To continue the upload, the client should call '
               '`POST /dataset/{id}/zip/{zipUploadId}/part`.')
        .param('id', 'The ID of the dataset.', paramType='path')
        .param('name', 'The name of the ZIP file.', paramType='form')
        .param('size', 'The size of the ZIP file, in bytes.', paramType='form', dataType='integer')
    )
    @access.user
    @loadmodel(model='dataset', plugin='isic_archive', level=AccessType.WRITE)
    def initZipUpload(self, dataset, params):
        params = self._decodeParams(params)
        self.requireParams(['name', 'size'], params)

        user = self.getCurrentUser()
        User().requireCreateDataset(user)

        # Require file name
        name = params['name'].strip()
        if not name:
            raise ValidationException('File name must be specified.', 'name')

        # Require integer size
        try:
            size = int(params['size'])
        except ValueError:
            raise RestException('Invalid file size.')

        # Require positive size
        if size <= 0:
            raise ValidationException('File size must be greater than zero.', 'size')

        # Create upload in the configured ZIP upload S3 assetstore
        assetstore = Assetstore().findOne(
            {'_id': Setting().get(PluginSettings.ZIP_UPLOAD_S3_ASSETSTORE_ID)})
        if not assetstore:
            raise RestException('ZIP upload S3 assetstore not configured.')

        upload = Upload().createUpload(
            user=user, name=name, parentType='dataset', parent=dataset, size=size,
            mimeType='application/zip', assetstore=assetstore, attachParent=True)

        return upload

    @describeRoute(
        Description('Upload a part of a ZIP file of images in a multi-part direct-to-S3 upload.')
        .notes('After the client initiates a multi-part upload of a ZIP file of images, '
               'this endpoint returns information for the client to make a subsequent HTTP '
               'request to upload a part of the file directly to S3.'
               '\n\n'
               'More specifically, this endpoint returns a JSON response in which the `s3` field '
               'contains the S3 request information. The client should make an HTTP request with '
               'the following properties to update a part of the file:\n\n'
               '|             |                                                     |\n'
               '|-------------|-----------------------------------------------------|\n'
               '| **Method**  | `s3.request.method`                                 |\n'
               '| **URL**     | `s3.request.url`                                    |\n'
               '| **Headers** | One for each key-value pair in `s3.request.headers` |\n'
               '|             | `Content-Length`: &lt;part size, in bytes&gt;       |\n'
               '|             | `Content-MD5`: base64-encoded MD5 digest of data    |\n'
               '| **Data**    | Part content                                        |\n'
               '|             |                                                     |\n'
               '\n\n'
               'This response to this request includes an `ETag` header. The client should parse '
               'this header and store its value along with the associated part number. The '
               'client will use these values later, when finalizing the upload.'
               '\n\n'
               'This S3 request is documented at '
               'https://docs.aws.amazon.com/AmazonS3/latest/API/mpUploadUploadPart.html.'
               '\n\n'
               'After uploading all the parts of the file, the client should call '
               '`POST /dataset/{id}/zip/{zipUploadId}/completion` to finalize the upload.')
        .param('id', 'The ID of the dataset.', paramType='path')
        .param('zipUploadId', 'The ID of the ZIP file upload.', paramType='path')
        .param('s3UploadId', 'S3 upload ID.', paramType='form')
        .param('partNumber', 'Part number, starting at 1.', paramType='form', dataType='integer')
        .param('contentLength', 'The size of the part, in bytes.', paramType='form',
               dataType='integer')
    )
    @access.user
    @loadmodel(map={'zipUploadId': 'upload'}, model='upload')
    @loadmodel(model='dataset', plugin='isic_archive', level=AccessType.WRITE)
    def addZipUploadPart(self, dataset, upload, params):
        params = self._decodeParams(params)
        self.requireParams(['s3UploadId', 'partNumber', 'contentLength'], params)

        user = self.getCurrentUser()
        User().requireCreateDataset(user)

        if upload['userId'] != user['_id']:
            raise AccessException('You did not initiate this upload.')

        try:
            partNumber = int(params['partNumber'])
        except ValueError:
            raise RestException('Invalid part number.')

        try:
            contentLength = int(params['contentLength'])
        except ValueError:
            raise RestException('Invalid content length.')

        # For direct-to-S3 upload, S3AssetstoreAdapter expects its 'chunk' argument to be
        # a string representation of the JSON object with keys: 's3UploadId', 'parentNumber',
        # and 'contentLength'.
        strParams = json.dumps({
            's3UploadId': params['s3UploadId'],
            'partNumber': partNumber,
            'contentLength': contentLength
        })
        upload = Upload().handleChunk(upload, chunk=strParams, filter=False, user=user)

        # Ensure 's3.request.headers' field exists
        upload['s3']['request'].setdefault('headers', {})

        return upload

    @describeRoute(
        Description('Finalize a direct-to-S3 upload of a ZIP file of images.')
        .notes('The client should call this endpoint once all the parts of the ZIP file are '
               'uploaded to S3.'
               '\n\n'
               'This endpoint returns a JSON response in which the `_id` field contains the '
               'ZIP file ID to use in subsequent requests, such as '
               '`POST /dataset/{id}/imageZip`.'
               '\n\n'
               '#### Single-part upload\n'
               'For a single-part upload, no further requests are necessary.'
               '\n\n'
               '#### Multi-part upload\n'
               '\n\n'
               'For a multi-part upload, this endpoint additionally returns an '
               '`s3` field that contains information to make an S3 request to complete the '
               'upload by assembling the parts. The client should make an HTTP request with '
               'the following properties to complete the upload:\n\n'
               '|             |                                                            |\n'
               '|-------------|------------------------------------------------------------|\n'
               '| **Method**  | `s3.request.method`                                        |\n'
               '| **URL**     | `s3.request.url`                                           |\n'
               '| **Headers** | One for each key-value pair in `s3.request.headers`        |\n'
               '|             | `Content-Length`: &lt;data size, in bytes&gt;              |\n'
               '|             | `Content-MD5`: base64-encoded MD5 digest of data           |\n'
               '| **Data**    | (See below)                                                |\n'
               '|             |                                                            |\n'
               '\n\n'
               'The data for this request is an XML string with root element '
               '`CompleteMultipartUpload`, and child `Part` elements, one for '
               'each uploaded part. Each `Part` element has two children: '
               '`PartNumber` and `ETag`. `PartNumber` elements should contain '
               'an integer that indicates the position of the part in the file, '
               'starting at 1. `ETag` elements should contain the ETag returned '
               'after uploading the part to S3.'
               '\n\n'
               'This S3 request is documented at '
               'https://docs.aws.amazon.com/AmazonS3/latest/API/mpUploadComplete.html.')
        .param('id', 'The ID of the dataset.', paramType='path')
        .param('zipUploadId', 'The ID of the ZIP file upload.', paramType='path')
    )
    @access.user
    @loadmodel(map={'zipUploadId': 'upload'}, model='upload')
    @loadmodel(model='dataset', plugin='isic_archive', level=AccessType.WRITE)
    def finalizeZipUpload(self, dataset, upload, params):
        user = self.getCurrentUser()
        User().requireCreateDataset(user)

        if upload['userId'] != user['_id']:
            raise AccessException('You did not initiate this upload.')

        file = Upload().finalizeUpload(upload)

        # TODO: remove this once a bug in upstream Girder is fixed
        file['attachedToType'] = ['dataset', 'isic_archive']
        file = File().save(file)

        additionalKeys = file.get('additionalFinalizeKeys', [])
        return File().filter(file, user=user, additionalKeys=additionalKeys)

    @describeRoute(
        Description('Cancel a partially completed direct-to-S3 upload of a ZIP file of images.')
        .notes('The client should call this endpoint to cancel a ZIP file upload before '
               'finalizing it. This deletes the uploaded parts from S3 and removes the '
               'ZIP file upload from the server.')
        .param('id', 'The ID of the dataset.', paramType='path')
        .param('zipUploadId', 'The ID of the ZIP file upload.', paramType='path')
    )
    @access.user
    @loadmodel(map={'zipUploadId': 'upload'}, model='upload')
    @loadmodel(model='dataset', plugin='isic_archive', level=AccessType.WRITE)
    def cancelZipUpload(self, dataset, upload, params):
        user = self.getCurrentUser()
        User().requireCreateDataset(user)

        if upload['userId'] != user['_id'] and not user['admin']:
            raise AccessException('You did not initiate this upload.')

        Upload().cancelUpload(upload)
        return {'message': 'Upload canceled.'}

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
        .param('id', 'The ID of the dataset.', paramType='path')
        .param('metadataFileId', 'The ID of the .csv metadata file.', paramType='form')
    )
    @access.user
    @loadmodel(model='dataset', plugin='isic_archive', level=AccessType.WRITE)
    def registerMetadata(self, dataset, params):
        params = self._decodeParams(params)
        self.requireParams(['metadataFileId'], params)
        user = self.getCurrentUser()

        metadataFile = File().load(
            params['metadataFileId'], user=user, level=AccessType.WRITE, exc=False)
        if not metadataFile:
            raise ValidationException('Invalid metadata file ID.', 'metadataFileId')
        if not self._checkFileFormat(metadataFile, CSV_FORMATS):
            raise ValidationException('File must be in .csv format.', 'metadataFileId')

        Dataset().registerMetadata(
            dataset=dataset, user=user, metadataFile=metadataFile, sendMail=True)
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
        Description('Apply registered metadata to a dataset.')
        .param('id', 'The ID of the dataset.', paramType='path')
        .param('fileId', 'The ID of the .csv metadata file.', paramType='path')
        .param('save', 'Whether to save the metadata to the dataset if validation succeeds.',
               dataType='boolean', default=False, paramType='form')
    )
    @access.user
    @loadmodel(model='file', map={'fileId': 'metadataFile'}, force=True)
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
