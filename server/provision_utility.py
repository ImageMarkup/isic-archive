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

from girder.constants import AccessType, SettingKey
from girder.utility.model_importer import ModelImporter


def getAdminUser():
    User = ModelImporter.model('user', 'isic_archive')
    # TODO: cache this?
    adminUser = User.findOne({'login': 'isic-admin'})
    if not adminUser:
        adminUser = User.createUser(
            login='isic-admin',
            password='isic-admin',
            firstName='ISIC Archive',
            lastName='Admin',
            email='admin@isic-archive.com',
            admin=True,
            public=False
        )
        adminUser['status'] = 'disabled'
        # TODO: subsequent re-saves of this user will re-enable it, until another user is created
        adminUser = User.save(adminUser, validate=False)
    return adminUser


def _provisionImages():
    Collection = ModelImporter.model('collection')
    Group = ModelImporter.model('group')

    if not Group.findOne({'name': 'Dataset Contributors'}):
        contributorsGroup = Group.createGroup(
            name='Dataset Contributors',
            creator=getAdminUser(),
            description='Users that can create datasets',
            public=True
        )
        Group.removeUser(contributorsGroup, getAdminUser())

    reviewerGroup = Group.findOne({'name': 'Dataset QC Reviewers'})
    if not reviewerGroup:
        reviewerGroup = Group.createGroup(
            name='Dataset QC Reviewers',
            creator=getAdminUser(),
            description='Users responsible for doing initial QC',
            public=True
        )
        Group.removeUser(reviewerGroup, getAdminUser())

    if not Collection.findOne({'name': 'Flagged Images'}):
        flaggedCollection = Collection.createCollection(
            name='Flagged Images',
            creator=getAdminUser(),
            description='Images that have been flagged for any reason',
            public=False,
            reuseExisting=False
        )
        flaggedCollection = Collection.setAccessList(
            doc=flaggedCollection,
            access={},
            save=False
        )
        Collection.setGroupAccess(
            doc=flaggedCollection,
            group=reviewerGroup,
            # TODO: make this a special access level
            level=AccessType.READ,
            save=True
        )

    imageCollection = Collection.createCollection(
        name='Lesion Images',
        creator=getAdminUser(),
        description='All public lesion image datasets',
        public=True,
        reuseExisting=True
    )
    Collection.setAccessList(
        doc=imageCollection,
        access={},
        save=True
    )


def _provisionSegmentationGroups():
    Group = ModelImporter.model('group')

    if not Group.findOne({'name': 'Segmentation Novices'}):
        segmentationNovicesGroup = Group.createGroup(
            name='Segmentation Novices',
            creator=getAdminUser(),
            description='Users able to tentatively segment lesion boundaries',
            public=True
        )
        Group.removeUser(segmentationNovicesGroup, getAdminUser())

    if not Group.findOne({'name': 'Segmentation Experts'}):
        segmentationExpertsGroup = Group.createGroup(
            name='Segmentation Experts',
            creator=getAdminUser(),
            description='Users able to definitively segment lesion boundaries',
            public=True
        )
        Group.removeUser(segmentationExpertsGroup, getAdminUser())


def _provisionStudies():
    Collection = ModelImporter.model('collection')
    Group = ModelImporter.model('group')

    studyAdminGroup = Group.findOne({'name': 'Study Administrators'})
    if not studyAdminGroup:
        studyAdminGroup = Group.createGroup(
            name='Study Administrators',
            creator=getAdminUser(),
            description='Annotation study creators and administrators',
            public=True
        )
        Group.removeUser(studyAdminGroup, getAdminUser())

    studiesCollection = Collection.createCollection(
        name='Annotation Studies',
        creator=getAdminUser(),
        description='Clinical feature annotation studies',
        public=True,
        reuseExisting=True
    )
    studiesCollection = Collection.setAccessList(
        doc=studiesCollection,
        access={},
        save=False
    )
    Collection.setGroupAccess(
        doc=studiesCollection,
        group=studyAdminGroup,
        # TODO: make this a special access level
        level=AccessType.READ,
        save=True
    )


def provisionDatabase():
    Setting = ModelImporter.model('setting')

    Setting.set(SettingKey.USER_DEFAULT_FOLDERS, 'none')

    _provisionImages()
    _provisionSegmentationGroups()
    _provisionStudies()
