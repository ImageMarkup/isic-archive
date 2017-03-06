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

import pytz

from girder.constants import AccessType
from tests import base

from .isic_base import IsicTestCase


def setUpModule():
    base.enabledPlugins.append('isic_archive')
    base.startServer()


def tearDownModule():
    base.stopServer()


class FeaturesetTestCase(IsicTestCase):
    def setUp(self):
        super(FeaturesetTestCase, self).setUp()

    def testFeatureset(self):
        Featureset = self.model('featureset', 'isic_archive')
        Group = self.model('group')
        Study = self.model('study', 'isic_archive')
        User = self.model('user', 'isic_archive')

        # Create a basic user
        resp = self.request(path='/user', method='POST', params={
            'email': 'basic-user@isic-archive.com',
            'login': 'basic-user',
            'firstName': 'basic',
            'lastName': 'user',
            'password': 'password'
        })
        self.assertStatusOk(resp)
        basicUser = User.findOne({'login': 'basic-user'})

        # Create a study admin user
        resp = self.request(path='/user', method='POST', params={
            'email': 'study-admin-user@isic-archive.com',
            'login': 'study-admin-user',
            'firstName': 'study admin',
            'lastName': 'user',
            'password': 'password'
        })
        self.assertStatusOk(resp)
        studyAdminUser = User.findOne({'login': 'study-admin-user'})
        studyAdminsGroup = Group.findOne({'name': 'Study Administrators'})
        Group.addUser(studyAdminsGroup, studyAdminUser, level=AccessType.READ)

        basicFeaturesetParams = {
            'name': '  Basic  ',
            'version': '1.0',
            'globalFeatures': [
                {
                    'id': 'quality',
                    'name': ['Quality'],
                    'options': [
                        {
                            'id': 'acceptable',
                            'name': 'Acceptable'
                        },
                        {
                            'id': 'unacceptable',
                            'name': 'Unacceptable'
                        }
                    ],
                    'type': 'radio'
                },
                {
                    'id': 'diagnosis',
                    'name': ['Diagnosis'],
                    'options': [
                        {
                            'id': 'benign',
                            'name': 'Benign'
                        },
                        {
                            'id': 'indeterminate',
                            'name': 'Indeterminate'
                        },
                        {
                            'id': 'malignant',
                            'name': 'Malignant'
                        }
                    ],
                    'type': 'radio'
                }
            ],
            'localFeatures': [
                {
                    'id': 'lesion',
                    'name': ['Lesion'],
                    'type': 'superpixel'
                },
                {
                    'id': 'skin',
                    'name': ['Normal Skin'],
                    'type': 'superpixel'
                }
            ]
        }

        # Try to create a featureset as anonymous
        resp = self.request(
            path='/featureset', method='POST', params=basicFeaturesetParams)
        self.assertStatus(resp, 401)

        # Try to create a featureset without privileges
        resp = self.request(
            path='/featureset', method='POST', user=basicUser,
            params=basicFeaturesetParams)
        self.assertStatus(resp, 403)

        # Try to create a featureset with an empty name
        tempFeaturesetParams = basicFeaturesetParams.copy()
        tempFeaturesetParams['name'] = ''
        resp = self.request(
            path='/featureset', method='POST', user=studyAdminUser,
            type='application/json', body=json.dumps(tempFeaturesetParams))
        self.assertStatus(resp, 400)

        # Try to create a featureset with an invalid version
        tempFeaturesetParams = basicFeaturesetParams.copy()
        tempFeaturesetParams['version'] = 'foo'
        resp = self.request(
            path='/featureset', method='POST', user=studyAdminUser,
            type='application/json', body=json.dumps(tempFeaturesetParams))
        self.assertStatus(resp, 400)

        # TODO: Try to create a featureset with invalid features

        # List all (nonexistent) featuresets
        resp = self.request(
            path='/featureset', method='GET')
        self.assertStatusOk(resp)
        self.assertEqual(resp.json, [])

        # Create a valid featureset
        resp = self.request(
            path='/featureset', method='POST', user=studyAdminUser,
            type='application/json', body=json.dumps(basicFeaturesetParams))
        self.assertStatusOk(resp)
        # Lookup the database entry, for access to non-deterministic details
        # like '_id' and 'created'
        basicFeatureset = Featureset.load(resp.json['_id'])

        # Check the list of all featuresets
        resp = self.request(
            path='/featureset', method='GET')
        self.assertStatusOk(resp)
        self.assertIsInstance(resp.json, list)
        self.assertEqual(len(resp.json), 1)
        self.assertDictEqual({
            '_id': str(basicFeatureset['_id']),
            'name': basicFeaturesetParams['name'].strip(),
            'version': float(basicFeaturesetParams['version']),
        }, resp.json[0])

        # Check featureset details as anonymous
        resp = self.request(
            path='/featureset/%s' % basicFeatureset['_id'], method='GET')
        self.assertStatusOk(resp)
        self.assertDictEqual({
            '_id': str(basicFeatureset['_id']),
            '_modelType': 'featureset',
            'name': basicFeaturesetParams['name'].strip(),
            'version': float(basicFeaturesetParams['version']),
            'created':
                basicFeatureset['created'].replace(tzinfo=pytz.UTC).isoformat(),
            'creator': {
                '_id': str(studyAdminUser['_id']),
                'name': User.obfuscatedName(studyAdminUser)
            },
            'globalFeatures': basicFeaturesetParams['globalFeatures'],
            'localFeatures': basicFeaturesetParams['localFeatures']
        }, resp.json)

        # Ensure that normal users don't get private creator info
        resp = self.request(
            path='/featureset/%s' % basicFeatureset['_id'], method='GET',
            user=basicUser)
        self.assertStatusOk(resp)
        self.assertDictEqual({
            '_id': str(studyAdminUser['_id']),
            'name': User.obfuscatedName(studyAdminUser)
        }, resp.json['creator'])

        # Ensure that study admin users do get private creator info
        resp = self.request(
            path='/featureset/%s' % basicFeatureset['_id'], method='GET',
            user=studyAdminUser)
        self.assertStatusOk(resp)
        self.assertDictEqual({
            '_id': str(studyAdminUser['_id']),
            'name': User.obfuscatedName(studyAdminUser),
            'firstName': studyAdminUser['firstName'],
            'lastName': studyAdminUser['lastName'],
            'login': studyAdminUser['login']
        }, resp.json['creator'])

        # Try to delete a featureset as anonymous
        resp = self.request(
            path='/featureset/%s' % basicFeatureset['_id'], method='DELETE')
        self.assertStatus(resp, 401)

        # Try to delete a featureset without privileges
        resp = self.request(
            path='/featureset/%s' % basicFeatureset['_id'], method='DELETE',
            user=basicUser)
        self.assertStatus(resp, 403)

        # Try to delete a featureset being used by a study
        resp = self.request(
            path='/study', method='POST', user=studyAdminUser,
            type='application/json', body=json.dumps({
                'name': 'Test Study',
                'featuresetId': str(basicFeatureset['_id']),
                'userIds': [],
                'imageIds': []
            }))
        self.assertStatusOk(resp)
        testStudy = Study.load(resp.json['_id'], force=True)
        resp = self.request(
            path='/featureset/%s' % basicFeatureset['_id'], method='DELETE',
            user=studyAdminUser)
        self.assertStatus(resp, 409)
        resp = self.request(
            path='/featureset', method='GET')
        self.assertStatusOk(resp)
        self.assertEqual(len(resp.json), 1)

        # TODO: Use the Study API, once it exists
        Study.remove(testStudy)

        # Delete an unused featureset
        resp = self.request(
            path='/featureset/%s' % basicFeatureset['_id'], method='DELETE',
            user=studyAdminUser, isJson=False)
        self.assertStatus(resp, 204)
        resp = self.request(
            path='/featureset', method='GET')
        self.assertStatusOk(resp)
        self.assertEqual(resp.json, [])
