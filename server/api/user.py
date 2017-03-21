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

from girder import events
from girder.api import access
from girder.api.describe import Description, describeRoute
from girder.api.rest import getCurrentUser, RestException
from girder.constants import AccessType
from girder.utility import mail_utils
from girder.utility.model_importer import ModelImporter


def attachUserPermissions(userResponse):
    User = ModelImporter.model('user', 'isic_archive')

    user = User.load(userResponse['_id'], exc=True, force=True)

    userResponse['permissions'] = {
        'acceptTerms': User.canAcceptTerms(user),
        'createDataset': User.canCreateDataset(user),
        'reviewDataset': User.canReviewDataset(user),
        'segmentationSkill': User.getSegmentationSkill(user),
        'adminStudy': User.canAdminStudy(user)
    }


def onGetUserAuthentication(event):
    userResponse = event.info['returnVal']['user']
    attachUserPermissions(userResponse)


def onGetUserMe(event):
    userResponse = event.info['returnVal']
    # It is possible for userResponse to be None, for anonymous users
    if userResponse:
        attachUserPermissions(userResponse)


def onPostUser(event):
    userResponse = event.info['returnVal']
    attachUserPermissions(userResponse)


def getUserEmail(user):
    User = ModelImporter.model('user', 'isic_archive')
    user = User.load(user['id'], force=True, exc=True)
    return user['email']


@access.user
@describeRoute(
    Description('Request permission to create datasets.'))
def requestCreateDatasetPermission(params):
    User = ModelImporter.model('user', 'isic_archive')
    Group = ModelImporter.model('group')
    currentUser = getCurrentUser()
    resp = {}
    if User.canCreateDataset(currentUser):
        resp['message'] = 'Dataset Contributor access granted.',
        resp['extra'] = 'hasPermission'
    else:
        # Request that user join group
        groupName = 'Dataset Contributors'
        group = Group.findOne({'name': groupName})
        if not group:
            raise RestException('Could not load group: %s' % groupName)
        resp['message'] = 'Dataset Contributor access requested. An administrator may contact ' \
                          'you via email (at %s) to process your request.' % currentUser['email']

        for request in Group.getFullRequestList(group):
            if request['id'] == currentUser['_id']:
                # Request for this user is already pending
                break
        else:
            # No request for this user yet
            Group.joinGroup(group, currentUser)

            # Send email to group moderators and administrators
            groupAcl = Group.getFullAccessList(group)
            groupModeratorEmails = [
                getUserEmail(user)
                for user in groupAcl['users']
                if user['level'] >= AccessType.WRITE
            ]
            host = mail_utils.getEmailUrlPrefix()
            html = mail_utils.renderTemplate(
                'datasetContributorRequest.mako',
                {
                    'user': currentUser,
                    'group': group,
                    'host': host,
                })
            mail_utils.sendEmail(
                to=groupModeratorEmails,
                subject='ISIC Archive: Dataset Contributor Request',
                text=html)

    return resp


@access.user
@describeRoute(
    Description('Accept Terms of Use.'))
def acceptTerms(params):
    User = ModelImporter.model('user', 'isic_archive')

    currentUser = getCurrentUser()
    if not User.canAcceptTerms(currentUser):
        User.acceptTerms(currentUser)
        User.save(currentUser)

    resp = {
        'message': 'Terms of Use accepted.',
        'extra': 'hasPermission'
    }
    return resp


def attachUserApi(user):
    events.bind('rest.get.user/authentication.after', 'onGetUserAuthentication',
                onGetUserAuthentication)
    events.bind('rest.get.user/me.after', 'onGetUserMe', onGetUserMe)
    events.bind('rest.post.user.after', 'onPostUser', onPostUser)
    user.route('POST', ('requestCreateDatasetPermission',), requestCreateDatasetPermission)
    user.route('POST', ('acceptTerms',), acceptTerms)
