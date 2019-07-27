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

import re

import cherrypy

from girder import events
from girder.api import access
from girder.api.describe import describeRoute, Description
from girder.api.rest import boundHandler
from girder.constants import AccessType, TokenScope
from girder.exceptions import RestException, ValidationException
from girder.models.group import Group
from girder.models.token import Token
from girder.utility import mail_utils

from .base import IsicResource
from ..models.user import User


def attachUserPermissions(userResponse):
    user = User().load(userResponse['_id'], exc=True, force=True)

    userResponse['permissions'] = {
        'acceptTerms': User().canAcceptTerms(user),
        'createDataset': User().canCreateDataset(user),
        'reviewDataset': User().canReviewDataset(user),
        'segmentationSkill': User().getSegmentationSkill(user),
        'adminStudy': User().canAdminStudy(user)
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


def onGetPasswordTemporaryId(event):
    userResponse = event.info['returnVal']['user']
    attachUserPermissions(userResponse)


def onSetCookie(event):
    cookie = cherrypy.response.cookie
    if 'girderToken' in cookie:
        host = cherrypy.request.base
        if re.search(r'://isic-archive\.com$', host):
            # Persist subdomain logins to the root domain
            # TODO: This makes the cookie available to any other Girder instance subdomains
            cookie['girderToken']['Domain'] = 'isic-archive.com'


def getUserEmail(user):
    user = User().load(user['id'], force=True, exc=True)
    return user['email']


_sharedContext = IsicResource()


@access.user
@describeRoute(
    Description('Request permission to create datasets.'))
@boundHandler(_sharedContext)
def requestCreateDatasetPermission(self, params):
    currentUser = self.getCurrentUser()
    resp = {}
    if User().canCreateDataset(currentUser):
        resp['message'] = 'Dataset Contributor access granted.',
        resp['extra'] = 'hasPermission'
    else:
        # Request that user join group
        groupName = 'Dataset Contributors'
        group = Group().findOne({'name': groupName})
        if not group:
            raise RestException(f'Could not load group: {groupName}')
        resp['message'] = 'Dataset Contributor access requested. An administrator may contact ' \
                          f'you via email (at {currentUser["email"]}) to process your request.'

        for request in Group().getFullRequestList(group):
            if request['id'] == currentUser['_id']:
                # Request for this user is already pending
                break
        else:
            # No request for this user yet
            Group().joinGroup(group, currentUser)

            # Send email to group moderators and administrators
            groupAcl = Group().getFullAccessList(group)
            groupModeratorEmails = [
                getUserEmail(user)
                for user in groupAcl['users']
                if user['level'] >= AccessType.WRITE
            ]
            if groupModeratorEmails:
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
@boundHandler(_sharedContext)
def acceptTerms(self, params):
    currentUser = self.getCurrentUser()
    if not User().canAcceptTerms(currentUser):
        User().acceptTerms(currentUser)
        User().save(currentUser)

    resp = {
        'message': 'Terms of Use accepted.',
        'extra': 'hasPermission'
    }
    return resp


@access.user
@describeRoute(
    Description('Pre-create a new user and issue them an invite.')
    .param('login', "The user's requested login.")
    .param('email', "The user's email address.")
    .param('firstName', "The user's first name.")
    .param('lastName', "The user's last name.")
    .param('validityPeriod', 'The number of days that the invite will remain valid.',
           required=False, dataType='float', default=60.0)
)
@boundHandler(_sharedContext)
def inviteUser(self, params):
    params = self._decodeParams(params)
    self.requireParams(['login', 'email', 'firstName', 'lastName'], params)
    if 'validityPeriod' in params:
        try:
            validityPeriod = float(params['validityPeriod'])
        except ValueError:
            raise ValidationException('Validity period must be a number.', 'validityPeriod')
    else:
        validityPeriod = 60.0

    currentUser = self.getCurrentUser()
    User().requireAdminStudy(currentUser)

    newUser = User().createUser(
        login=params['login'],
        password=None,
        email=params['email'],
        firstName=params['firstName'],
        lastName=params['lastName']
    )

    token = Token().createToken(
        newUser, days=validityPeriod,
        scope=[TokenScope.TEMPORARY_USER_AUTH])

    inviteUrl = f'{mail_utils.getEmailUrlPrefix()}/#user/{newUser["_id"]}/rsvp/{token["_id"]}'

    html = mail_utils.renderTemplate(
        'inviteUser.mako',
        {
            'newUser': newUser,
            'inviteUrl': inviteUrl,
        })
    mail_utils.sendEmail(
        to=newUser['email'],
        subject='ISIC Archive: Invitation',
        text=html)

    return {
        'newUser': User().filterSummary(newUser, currentUser),
        'inviteUrl': inviteUrl
    }


def attachUserApi(user):
    events.bind('rest.get.user/authentication.after', 'onGetUserAuthentication',
                onGetUserAuthentication)
    events.bind('rest.get.user/me.after', 'onGetUserMe', onGetUserMe)
    events.bind('rest.post.user.after', 'onPostUser', onPostUser)
    events.bind('rest.get.user/password/temporary/:id.after', 'onGetPasswordTemporaryId',
                onGetPasswordTemporaryId)

    # TODO: Bind these in a more general way, as other places (e.g. OAuth) may also set the cookie
    events.bind('rest.post.user.after', 'onSetCookie', onSetCookie)
    events.bind('rest.get.user/authentication.after', 'onSetCookie', onSetCookie)
    events.bind('rest.get.user/password/temporary/:id.after', 'onSetCookie', onSetCookie)
    events.bind('rest.put.user/:id/verification.after', 'onSetCookie', onSetCookie)

    user.route('POST', ('requestCreateDatasetPermission',), requestCreateDatasetPermission)
    user.route('POST', ('acceptTerms',), acceptTerms)
    user.route('POST', ('invite',), inviteUser)
