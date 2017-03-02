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

from girder.constants import AccessType
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

    def _uploadDataset(self, uploaderUser, zipName, zipContentNames,
                       datasetName, datasetDescription):
        Dataset = self.model('dataset', 'isic_archive')
        Folder = self.model('folder')
        Upload = self.model('upload')

        # Create a ZIP file of images
        testDataDir = os.path.join(
            os.environ['GIRDER_TEST_DATA_PREFIX'], 'plugins', 'isic_archive')
        zipStream = BytesIO()
        zipGen = ZipGenerator(zipName)
        for fileName in zipContentNames:
            with open(os.path.join(testDataDir, fileName), 'rb') as fileObj:
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
        Group = self.model('group')
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
                'Location': '/uda/gallery#/qc/%s' % reviewId
            }, resp.headers)
