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

import os

from six import BytesIO

from girder.utility.ziputil import ZipGenerator
from tests import base

from .isic_base import IsicTestCase


def setUpModule():
    base.enabledPlugins.append('isic_archive')
    base.startServer()


def tearDownModule():
    base.stopServer()


class UploadTestCase(IsicTestCase):
    def testUpload(self):
        Folder = self.model('folder')
        print Folder.database
        Upload = self.model('upload')
        User = self.model('user', 'isic_archive')

        testDataDir = os.path.join(
            os.environ['GIRDER_TEST_DATA_PREFIX'], 'plugins', 'isic_archive')
        uploadFileNames = [
            'test_1_small_1.jpg',
            'test_1_small_2.jpg',
            'test_1_small_3.jpg',
            'test_1_large_1.jpg',
            'test_1_large_2.jpg'
        ]

        # Create a ZIP file of images
        zipGen = ZipGenerator('test_1')
        for fileName in uploadFileNames:
            with open(os.path.join(testDataDir, fileName), 'rb') as fileObj:
                zipGen.addFile(lambda: fileObj, fileName)
        zipStream = BytesIO(zipGen.footer())
        zipStream.seek(0, 2)
        zipSize = zipStream.tell()
        zipStream.seek(0)

        # Create new folders in the uploader user's home
        uploaderUser = User.findOne({'login': 'uploader-user'})
        self.assertIsNotNone(uploaderUser)

        resp = self.request(
            path='/folder', method='POST', user=uploaderUser, params={
                'parentType': 'user',
                'parentId': str(uploaderUser['_id']),
                'name': 'isic_upload_1'
            })
        self.assertStatusOk(resp)
        uploadZipFolder = resp.json

        resp = self.request(
            path='/folder', method='POST', user=uploaderUser, params={
                'parentType': 'user',
                'parentId': str(uploaderUser['_id']),
                'name': 'isic_upload_2'
            })
        self.assertStatusOk(resp)
        uploadCsvFolder = resp.json

        # Uploading files is complicated via REST, so upload the ZIP via models
        # No special behavior should be attached to uploading a plain ZIP file
        Upload.uploadFromFile(
            obj=zipStream,
            size=zipSize,
            name='test_dataset_1.zip',
            parentType='folder',
            parent=Folder.load(uploadZipFolder['_id'], force=True),
            user=uploaderUser,
            mimeType='application/zip'
        )

        # Create a new dataset
        resp = self.request(
            path='/dataset', method='POST', user=uploaderUser, params={
                'uploadFolderId': uploadZipFolder['_id'],
                'name': 'test_dataset_1',
                'owner': 'Test Organization',
                'description': 'A test dataset',
                'license': 'CC-0',
                'signature': 'Test Uploader',
                'anonymous': False,
                'attribution': 'Test Organization'
            })
        self.assertStatusOk(resp)
        dataset = resp.json

        # Upload the CSV metadata file
        csvPath = os.path.join(testDataDir, 'test_1_metadata.csv')
        with open(csvPath, 'rb') as csvStream:
            Upload.uploadFromFile(
                obj=csvStream,
                size=os.path.getsize(csvPath),
                name='test_1_metadata.csv',
                parentType='folder',
                parent=Folder.load(uploadCsvFolder['_id'], force=True),
                user=uploaderUser,
                mimeType='text/csv'
            )

        # Register metadata with dataset
        resp = self.request(
            path='/dataset/%s/metadata' % dataset['_id'], method='POST',
            user=uploaderUser, params={
                'uploadFolderId': uploadCsvFolder['_id'],
            })
        self.assertStatusOk(resp)
        dataset = resp.json
        self.assertHasKeys(dataset['meta'], ['metadataFiles'])
        self.assertEqual(len(dataset['meta']['metadataFiles']), 1)
        self.assertHasKeys(dataset['meta']['metadataFiles'][0],
                           ('fileId', 'time'))
