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
from girder.utility.model_importer import ModelImporter


def attachUserPermissions(userResponse):
    User = ModelImporter.model('user', 'isic_archive')

    user = User.load(userResponse['_id'], exc=True, force=True)

    userResponse['permissions'] = {
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


def attachUserApi():
    events.bind('rest.get.user/authentication.after',
                'onGetUserAuthentication', onGetUserAuthentication)
    events.bind('rest.get.user/me.after',
                'onGetUserMe', onGetUserMe)
    events.bind('rest.post.user.after',
                'onPostUser', onPostUser)
