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

from girder.constants import AccessType
from tests import base

from .isic_base import IsicTestCase


def setUpModule():
    # This should be the first module to run in the testing pipeline
    base.dropTestDatabase()
    # base.dropFsAssetstore()  # TODO: do this

    base.enabledPlugins.append('isic_archive')
    base.startServer()


def tearDownModule():
    base.stopServer()


class UserTestCase(IsicTestCase):
    def testBasicUser(self):
        User = self.model('user', 'isic_archive')

        # Create a basic user
        resp = self.request(path='/user', method='POST', params={
            'email': 'test-user@isic-archive.com',
            'login': 'test-user',
            'firstName': 'test',
            'lastName': 'user',
            'password': 'password'
        })
        self.assertStatusOk(resp)
        testUser = User.findOne({'login': 'test-user'})

        # Ensure creation returns permissions
        negativePermissions = {
            'acceptTerms': False,
            'createDataset': False,
            'reviewDataset': False,
            'segmentationSkill': None,
            'adminStudy': False
        }
        self.assertDictContainsSubset({
            'permissions': negativePermissions
        }, resp.json)

        # Ensure login returns permissions
        resp = self.request(path='/user/authentication', method='GET',
                            basicAuth='test-user:password')
        self.assertStatusOk(resp)
        self.assertDictContainsSubset({
            'permissions': negativePermissions
        }, resp.json['user'])

        # Ensure get user returns permissions
        resp = self.request(path='/user/me', method='GET', user=testUser)
        self.assertStatusOk(resp)
        self.assertDictContainsSubset({
            'permissions': negativePermissions
        }, resp.json)

        # Ensure get user for anonymous still succeeds
        resp = self.request(path='/user/me', method='GET')
        self.assertStatusOk(resp)
        self.assertIsNone(resp.json)

        # Ensure user is private
        resp = self.request(path='/user/%s' % testUser['_id'], method='GET')
        self.assertStatus(resp, 401)

        # Ensure accept terms works
        resp = self.request(path='/user/acceptTerms', method='POST',
                            user=testUser)
        self.assertStatusOk(resp)
        self.assertDictContainsSubset({
            'extra': 'hasPermission'
        }, resp.json)

        resp = self.request(path='/user/me', method='GET', user=testUser)
        self.assertStatusOk(resp)
        acceptedTermsPermissions = negativePermissions.copy()
        acceptedTermsPermissions['acceptTerms'] = True
        self.assertDictContainsSubset({
            'permissions': acceptedTermsPermissions
        }, resp.json)

        # Ensure accepting terms twice is idempotent
        testUser = User.findOne({'login': 'test-user'})
        uploaderUserAcceptTermsTime = testUser['acceptTerms']
        resp = self.request(path='/user/acceptTerms', method='POST',
                            user=testUser)
        self.assertStatusOk(resp)
        self.assertDictContainsSubset({
            'extra': 'hasPermission'
        }, resp.json)
        testUser = User.findOne({'login': 'test-user'})
        self.assertEqual(testUser['acceptTerms'],
                         uploaderUserAcceptTermsTime)

    def testUploaderUser(self):
        Group = self.model('group')
        User = self.model('user', 'isic_archive')

        # Create an uploader admin
        resp = self.request(path='/user', method='POST', params={
            'email': 'uploader-admin@isic-archive.com',
            'login': 'uploader-admin',
            'firstName': 'uploader',
            'lastName': 'admin',
            'password': 'password'
        })
        self.assertStatusOk(resp)
        uploaderAdmin = User.findOne({'login': 'uploader-admin'})
        contributorsGroup = Group.findOne({'name': 'Dataset Contributors'})
        contributorsGroup = Group.addUser(
            contributorsGroup, uploaderAdmin, level=AccessType.WRITE)

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

        # TODO: check if a user can upload without agreeing to terms

        # Ensure request create dataset permission works
        resp = self.request(path='/user/requestCreateDatasetPermission',
                            method='POST', user=uploaderUser)
        self.assertStatusOk(resp)

        # TODO: Ensure that an email was just sent

        # Ensure that the user can't create datasets yet
        resp = self.request(path='/user/me', method='GET', user=uploaderUser)
        self.assertStatusOk(resp)
        self.assertEqual(resp.json['permissions']['createDataset'], False)

        # Ensure that a join request is pending
        contributorsGroup = Group.findOne({'name': 'Dataset Contributors'})
        for user in Group.getFullRequestList(contributorsGroup):
            if user['id'] == uploaderUser['_id']:
                break
        else:
            self.fail('Group join request not found.')

        # TODO: Ensure that a second request does not send an email

        # Add the user, then ensure they can create datasets
        Group.inviteUser(
            contributorsGroup, uploaderUser, level=AccessType.READ)
        resp = self.request(path='/user/me', method='GET', user=uploaderUser)
        self.assertStatusOk(resp)
        self.assertEqual(resp.json['permissions']['createDataset'], True)
