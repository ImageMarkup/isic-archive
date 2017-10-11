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

import datetime
import json
import os

from six import BytesIO

from girder.constants import AccessType
from girder.utility import parseTimestamp
from girder.utility.ziputil import ZipGenerator
from tests import base

from .isic_base import IsicTestCase


def setUpModule():
    base.enabledPlugins.append('isic_archive')
    base.startServer()


def tearDownModule():
    base.stopServer()


class UploadTestCase(IsicTestCase):
    def setUp(self):
        super(UploadTestCase, self).setUp()

        # Set up girder_worker
        from girder.plugins import worker
        Setting = self.model('setting')
        Setting.set(
            worker.PluginSettings.BROKER,
            'mongodb://localhost:27017/girder_worker')
        Setting.set(
            worker.PluginSettings.BACKEND,
            'mongodb://localhost:27017/girder_worker')
        # TODO: change this to 'amqp://guest@127.0.0.1/' for RabbitMQ

        self.testDataDir = os.path.join(
            os.environ['GIRDER_TEST_DATA_PREFIX'], 'plugins', 'isic_archive')

    def _uploadDataset(self, uploaderUser, zipName, zipContentNames,
                       datasetName, datasetDescription):
        Dataset = self.model('dataset', 'isic_archive')
        Folder = self.model('folder')
        Upload = self.model('upload')

        # Create a ZIP file of images
        zipStream = BytesIO()
        zipGen = ZipGenerator(zipName)
        for fileName in zipContentNames:
            with open(os.path.join(self.testDataDir, fileName), 'rb') as \
                    fileObj:
                for data in zipGen.addFile(lambda: fileObj, fileName):
                    zipStream.write(data)
        zipStream.write(zipGen.footer())
        # Seek to the end of the stream
        zipStream.seek(0, 2)
        zipSize = zipStream.tell()
        zipStream.seek(0)

        # Create new folders in the uploader user's home
        resp = self.request(
            path='/folder', method='POST', user=uploaderUser, params={
                'parentType': 'user',
                'parentId': str(uploaderUser['_id']),
                'name': '%s_upload_folder' % zipName
            })
        self.assertStatusOk(resp)
        uploadZipFolder = Folder.load(resp.json['_id'], force=True)

        # Uploading files is complicated via REST, so upload the ZIP via models
        # No special behavior should be attached to uploading a plain ZIP file
        zipFile = Upload.uploadFromFile(
            obj=zipStream,
            size=zipSize,
            name='%s.zip' % zipName,
            parentType='folder',
            parent=uploadZipFolder,
            user=uploaderUser,
            mimeType='application/zip'
        )

        self.assertNoMail()
        resp = self.request(
            path='/dataset', method='POST', user=uploaderUser, params={
                'zipFileId': str(zipFile['_id']),
                'name': datasetName,
                'owner': 'Test Organization',
                'description': datasetDescription,
                'license': 'CC-0',
                'signature': 'Test Uploader',
                'anonymous': False,
                'attribution': 'Test Organization'
            })
        self.assertStatusOk(resp)
        dataset = Dataset.findOne({'name': datasetName})
        self.assertIsNotNone(dataset)
        self.assertEqual(str(dataset['_id']), resp.json['_id'])

        # Uploader user and reviewer user should receive emails
        self.assertMails(count=2)

        return dataset

    def testUploadDataset(self):
        File = self.model('file')
        Folder = self.model('folder')
        Group = self.model('group')
        Upload = self.model('upload')
        User = self.model('user', 'isic_archive')

        # Create a reviewer user that will receive notification emails
        resp = self.request(path='/user', method='POST', params={
            'email': 'reviewer-user@isic-archive.com',
            'login': 'reviewer-user',
            'firstName': 'reviewer',
            'lastName': 'user',
            'password': 'password'
        })
        self.assertStatusOk(resp)
        reviewerUser = User.findOne({'login': 'reviewer-user'})
        reviewersGroup = Group.findOne({'name': 'Dataset QC Reviewers'})
        Group.addUser(reviewersGroup, reviewerUser, level=AccessType.READ)

        # Create an uploader user
        resp = self.request(path='/user', method='POST', params={
            'email': 'uploader-user@isic-archive.com',
            'login': 'uploader-user',
            'firstName': 'uploader',
            'lastName': 'user',
            'password': 'password'
        })
        self.assertStatusOk(resp)
        uploaderUser = User.findOne({'login': 'uploader-user'})
        contributorsGroup = Group.findOne({'name': 'Dataset Contributors'})
        Group.addUser(contributorsGroup, uploaderUser, level=AccessType.READ)

        # Create and upload two ZIP files of images
        publicDataset = self._uploadDataset(
            uploaderUser=uploaderUser,
            zipName='test_zip_1',
            zipContentNames=['test_1_small_1.jpg', 'test_1_small_2.jpg',
                             'test_1_large_1.jpg'],
            datasetName='test_dataset_1',
            datasetDescription='A public test dataset'
        )
        privateDataset = self._uploadDataset(
            uploaderUser=uploaderUser,
            zipName='test_zip_2',
            zipContentNames=['test_1_small_3.jpg', 'test_1_large_2.jpg'],
            datasetName='test_dataset_2',
            datasetDescription='A private test dataset'
        )

        # Ensure that ordinary users aren't getting review tasks
        resp = self.request(
            path='/task/me/review', method='GET')
        self.assertStatus(resp, 401)
        resp = self.request(
            path='/task/me/review', method='GET', user=uploaderUser)
        self.assertStatus(resp, 403)

        # Ensure that reviewer users are getting tasks
        resp = self.request(
            path='/task/me/review', method='GET', user=reviewerUser)
        self.assertStatusOk(resp)
        reviewTasks = resp.json
        self.assertEqual(len(reviewTasks), 2)
        self.assertIn({
            'dataset': {
                '_id': str(publicDataset['_id']),
                'name': publicDataset['name']},
            'count': 3
        }, reviewTasks)
        self.assertIn({
            'dataset': {
                '_id': str(privateDataset['_id']),
                'name': privateDataset['name']},
            'count': 2
        }, reviewTasks)

        # Ensure that review task redirects are working
        resp = self.request(
            path='/task/me/review/redirect', method='GET', user=reviewerUser)
        self.assertStatus(resp, 400)
        for reviewTask in reviewTasks:
            reviewId = reviewTask['dataset']['_id']
            resp = self.request(
                path='/task/me/review/redirect', method='GET',
                params={'datasetId': reviewId}, user=reviewerUser, isJson=False)
            self.assertStatus(resp, 307)
            self.assertDictContainsSubset({
                'Location': '/markup/gallery#/qc/%s' % reviewId
            }, resp.headers)

        # Accept all images
        resp = self.request(
            path='/dataset/%s/review' % publicDataset['_id'], method='GET', user=reviewerUser)
        self.assertStatusOk(resp)
        self.assertEqual(len(resp.json), 3)
        imageIds = [image['_id'] for image in resp.json]
        resp = self.request(
            path='/dataset/%s/review' % publicDataset['_id'], method='POST', user=reviewerUser,
            params={
                'accepted': json.dumps(imageIds),
                'flagged': []
            })
        self.assertStatusOk(resp)

        # Test metadata registration
        resp = self.request(
            path='/folder', method='POST', user=uploaderUser, params={
                'parentType': 'user',
                'parentId': str(uploaderUser['_id']),
                'name': 'test_1_metadata_folder'
            })
        self.assertStatusOk(resp)
        uploadCsvFolder = Folder.load(resp.json['_id'], force=True)

        # Upload the CSV metadata file
        csvPath = os.path.join(self.testDataDir, 'test_1_metadata.csv')
        with open(csvPath, 'rb') as csvStream:
            metadataFile = Upload.uploadFromFile(
                obj=csvStream,
                size=os.path.getsize(csvPath),
                name='test_1_metadata.csv',
                parentType='folder',
                parent=uploadCsvFolder,
                user=uploaderUser,
                mimeType='text/csv'
            )

        # Attempt to register metadata as invalid users
        resp = self.request(
            path='/dataset/%s/metadata' % publicDataset['_id'], method='POST',
            params={
                'metadataFileId': metadataFile['_id']
            })
        self.assertStatus(resp, 401)
        resp = self.request(
            path='/dataset/%s/metadata' % publicDataset['_id'], method='POST',
            user=reviewerUser, params={
                'metadataFileId': metadataFile['_id']
            })
        self.assertStatus(resp, 403)

        # Attempt to register metadata with invalid parameters
        resp = self.request(
            path='/dataset/%s/metadata' % publicDataset['_id'], method='POST',
            user=uploaderUser)
        self.assertStatus(resp, 400)
        self.assertIn('required', resp.json['message'].lower())
        resp = self.request(
            path='/dataset/%s/metadata' % publicDataset['_id'], method='POST',
            user=uploaderUser, params={
                'metadataFileId': 'bad_id'
            })
        self.assertStatus(resp, 400)
        self.assertIn('invalid', resp.json['message'].lower())
        resp = self.request(
            path='/dataset/%s/metadata' % publicDataset['_id'], method='POST',
            user=uploaderUser, params={
                # TODO: find a cleaner way to pass a file with the wrong format
                'metadataFileId': File.findOne({
                    'mimeType': 'application/zip'})['_id'],
            })
        self.assertStatus(resp, 400)
        self.assertIn('format', resp.json['message'].lower())

        # Attempt to list registered metadata as invalid users
        resp = self.request(
            path='/dataset/%s/metadata' % publicDataset['_id'], method='GET')
        self.assertStatus(resp, 401)
        resp = self.request(
            path='/dataset/%s/metadata' % publicDataset['_id'], method='GET',
            user=uploaderUser)
        self.assertStatus(resp, 403)

        # List (empty) registered metadata
        resp = self.request(
            path='/dataset/%s/metadata' % publicDataset['_id'], method='GET',
            user=reviewerUser)
        self.assertStatusOk(resp)
        self.assertEqual(resp.json, [])

        # Register metadata with dataset
        self.assertNoMail()
        resp = self.request(
            path='/dataset/%s/metadata' % publicDataset['_id'], method='POST',
            user=uploaderUser, params={
                'metadataFileId': metadataFile['_id']
            })
        self.assertStatusOk(resp)
        # Reviewer user should receive email
        self.assertMails(count=1)

        # List registered metadata
        resp = self.request(
            path='/dataset/%s/metadata' % publicDataset['_id'],
            user=reviewerUser)
        self.assertStatusOk(resp)
        self.assertIsInstance(resp.json, list)
        self.assertEqual(len(resp.json), 1)
        # Check the 'time' field separately, as we don't know what it will be
        self.assertIn('time', resp.json[0])
        self.assertLess(parseTimestamp(resp.json[0]['time']),
                        datetime.datetime.utcnow())
        self.assertDictEqual({
            'file': {
                '_id': str(metadataFile['_id']),
                'name': metadataFile['name']
            },
            'user': {
                '_id': str(uploaderUser['_id']),
                'name': User.obfuscatedName(uploaderUser)
            },
            # This is actually checked above
            'time': resp.json[0]['time']
        }, resp.json[0])

        # Test applying metadata
        resp = self.request(
            path='/dataset/%s/metadata/%s' % (publicDataset['_id'], metadataFile['_id']),
            method='POST', user=uploaderUser, params={
                'save': False
            })
        self.assertStatusOk(resp)
        self.assertIn('errors', resp.json)
        self.assertIn('warnings', resp.json)
        self.assertEqual([], resp.json['errors'])
        self.assertEqual(
            resp.json['warnings'], [
                {'description':
                 'on CSV row 4: no images found that match \'filename\': \'test_1_small_3.jpg\''},
                {'description':
                 'on CSV row 6: no images found that match \'filename\': \'test_1_large_2.jpg\''},
                {'description':
                 'unrecognized field \'age_approx\' will be added to unstructured metadata'},
                {'description':
                 'unrecognized field \'isic_source_name\' will be added to unstructured metadata'}
            ])
