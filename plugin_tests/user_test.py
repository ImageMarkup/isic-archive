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
        self.assertIsNotNone(testUser)

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
        self.assertIsNotNone(uploaderAdmin)
        contributorsGroup = Group.findOne({'name': 'Dataset Contributors'})
        self.assertIsNotNone(contributorsGroup)
        Group.addUser(contributorsGroup, uploaderAdmin, level=AccessType.WRITE)

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
        self.assertIsNotNone(uploaderUser)

        # TODO: check if a user can upload without agreeing to terms

        # Ensure request create dataset permission works
        resp = self.request(path='/user/requestCreateDatasetPermission',
                            method='POST', user=uploaderUser)
        self.assertStatusOk(resp)

        self.assertMails(count=1)

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

        self.assertNoMail()

        # Add the user, then ensure they can create datasets
        Group.inviteUser(contributorsGroup, uploaderUser, level=AccessType.READ)
        resp = self.request(path='/user/me', method='GET', user=uploaderUser)
        self.assertStatusOk(resp)
        self.assertEqual(resp.json['permissions']['createDataset'], True)

    def testReviewerUser(self):
        Group = self.model('group')
        User = self.model('user', 'isic_archive')

        # Create a reviewer user
        resp = self.request(path='/user', method='POST', params={
            'email': 'reviewer-user@isic-archive.com',
            'login': 'reviewer-user',
            'firstName': 'reviewer',
            'lastName': 'user',
            'password': 'password'
        })
        self.assertStatusOk(resp)
        reviewerUser = User.findOne({'login': 'reviewer-user'})
        self.assertIsNotNone(reviewerUser)

        # Add the user to the reviewers group
        reviewersGroup = Group.findOne({'name': 'Dataset QC Reviewers'})
        self.assertIsNotNone(reviewersGroup)
        Group.addUser(reviewersGroup, reviewerUser, level=AccessType.READ)

        # Ensure they can review datasets
        resp = self.request(path='/user/me', method='GET', user=reviewerUser)
        self.assertStatusOk(resp)
        self.assertEqual(resp.json['permissions']['reviewDataset'], True)

    def testStudyAdminUser(self):
        Group = self.model('group')
        User = self.model('user', 'isic_archive')

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
        self.assertIsNotNone(studyAdminUser)

        # Add the user to the study admins group
        studyAdminsGroup = Group.findOne({'name': 'Study Administrators'})
        self.assertIsNotNone(studyAdminsGroup)
        Group.addUser(studyAdminsGroup, studyAdminUser, level=AccessType.READ)

        # Ensure they can admin studies
        resp = self.request(path='/user/me', method='GET', user=studyAdminUser)
        self.assertStatusOk(resp)
        self.assertEqual(resp.json['permissions']['adminStudy'], True)

    def testInviteNewUser(self):
        Group = self.model('group')
        User = self.model('user', 'isic_archive')

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
        self.assertIsNotNone(studyAdminUser)

        # Ensure that user doesn't have permission to invite a new user, yet
        resp = self.request(path='/user/invite', method='POST', params={
            'login': 'invited-user',
            'email': 'invited-user@isic-archive.com',
            'firstName': 'invited',
            'lastName': 'user'
        }, user=studyAdminUser)
        self.assertStatus(resp, 403)

        # Add the user to the study admins group
        studyAdminsGroup = Group.findOne({'name': 'Study Administrators'})
        self.assertIsNotNone(studyAdminsGroup)
        Group.addUser(studyAdminsGroup, studyAdminUser, level=AccessType.READ)

        # Ensure that user can invite a new user
        resp = self.request(path='/user/invite', method='POST', params={
            'login': 'invited-user',
            'email': 'invited-user@isic-archive.com',
            'firstName': 'invited',
            'lastName': 'user'
        }, user=studyAdminUser)
        self.assertStatusOk(resp)
        self.assertHasKeys(resp.json, ('newUser', 'inviteUrl'))
        self.assertHasKeys(resp.json['newUser'], ('login', 'firstName', 'lastName', 'name'))
        self.assertEqual(resp.json['newUser']['login'], 'invited-user')
        self.assertEqual(resp.json['newUser']['firstName'], 'invited')
        self.assertEqual(resp.json['newUser']['lastName'], 'user')
        self.assertTrue(resp.json['newUser']['name'])
        self.assertTrue(resp.json['inviteUrl'])

        self.assertMails(count=1)

        # Ensure that user can invite a new user and specify the validity period
        resp = self.request(path='/user/invite', method='POST', params={
            'login': 'invited-user2',
            'email': 'invited-user2@isic-archive.com',
            'firstName': 'invited',
            'lastName': 'user2',
            'validityPeriod': 15.0
        }, user=studyAdminUser)
        self.assertStatusOk(resp)
        self.assertHasKeys(resp.json, ('newUser', 'inviteUrl'))
        self.assertHasKeys(resp.json['newUser'], ('login', 'firstName', 'lastName', 'name'))
        self.assertEqual(resp.json['newUser']['login'], 'invited-user2')
        self.assertEqual(resp.json['newUser']['firstName'], 'invited')
        self.assertEqual(resp.json['newUser']['lastName'], 'user2')
        self.assertTrue(resp.json['newUser']['name'])
        self.assertTrue(resp.json['inviteUrl'])

        self.assertMails(count=1)

        # Test sending an invalid value for the validity period
        resp = self.request(path='/user/invite', method='POST', params={
            'login': 'invited-user3',
            'email': 'invited-user3@isic-archive.com',
            'firstName': 'invited',
            'lastName': 'user3',
            'validityPeriod': 'invalid'
        }, user=studyAdminUser)
        self.assertValidationError(resp, field='validityPeriod')
