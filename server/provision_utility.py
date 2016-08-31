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
from girder.utility.model_importer import ModelImporter

from . import constants


def onUserCreated(event):
    User = ModelImporter.model('user')
    Group = ModelImporter.model('group')
    user = event.info

    # make all users private
    user['public'] = False
    if user['login'] != 'udastudy':
        User.setGroupAccess(
            doc=user,
            group=Group.findOne({'name': 'Study Administrators'}),
            level=AccessType.READ,
            save=False
        )
    User.save(user)


def getAdminUser():
    User = ModelImporter.model('user')
    # TODO: cache this?
    adminUser = User.findOne({'login': 'udastudy'})
    if not adminUser:
        adminUser = ModelImporter.model('user').createUser(
            login='udastudy',
            password='isicarchive',
            firstName='ISIC Archive',
            lastName='Admin',
            email='admin@isic-archive.com',
            admin=True,
            public=False
        )
    return adminUser


def _provisionDefaultFeatureset():
    Featureset = ModelImporter.model('featureset', 'isic_archive')

    if not Featureset.findOne({'name': 'Basic'}):
        Featureset.createFeatureset(
            name='Basic',
            version=1.0,
            creator=getAdminUser(),
            globalFeatures=[
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
            localFeatures=[
                {
                    'id': 'lesion',
                    'name': ['Lesion'],
                    'type': 'check'
                },
                {
                    'id': 'skin',
                    'name': ['Normal Skin'],
                    'type': 'check'
                },
            ]
        )


def _provisionImages():
    Collection = ModelImporter.model('collection')
    Group = ModelImporter.model('group')

    phase0Collection = Collection.createCollection(
        name='Phase 0',
        creator=getAdminUser(),
        description='Images to QC',
        public=False,
        reuseExisting=True
    )

    phase0Group = Group.findOne({'name': 'Phase 0'})
    if not phase0Group:
        phase0Group = Group.createGroup(
            name='Phase 0',
            creator=getAdminUser(),
            description='Users responsible for doing initial QC',
            public=True
        )
        Group.removeUser(phase0Group, getAdminUser())

    Collection.setGroupAccess(
        doc=phase0Collection,
        group=phase0Group,
        # TODO: make this a special access level
        level=AccessType.READ,
        save=True
    )

    if not Group.findOne({'name': 'Dataset Contributors'}):
        contributorsGroup = Group.createGroup(
            name='Dataset Contributors',
            creator=getAdminUser(),
            description='Users that can create datasets',
            public=True
        )
        Group.removeUser(contributorsGroup, getAdminUser())

    Collection.createCollection(
        name='Flagged Images',
        creator=getAdminUser(),
        description='Images that have been flagged for any reason',
        public=False,
        reuseExisting=True
    )

    Collection.createCollection(
        name='Lesion Images',
        creator=getAdminUser(),
        description='All public lesion image datasets',
        public=True,
        reuseExisting=True
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

    studiesCollection = Collection.createCollection(
        name='Annotation Studies',
        creator=getAdminUser(),
        description='Clinical feature annotation studies',
        public=True,
        reuseExisting=True
    )

    studyAdminGroup = Group.findOne({'name': 'Study Administrators'})
    if not studyAdminGroup:
        studyAdminGroup = Group.createGroup(
            name='Study Administrators',
            creator=getAdminUser(),
            description='Annotation study creators and administrators',
            public=True
        )
        Group.removeUser(studyAdminGroup, getAdminUser())

    Collection.setGroupAccess(
        doc=studiesCollection,
        group=studyAdminGroup,
        # TODO: make this a special access level
        level=AccessType.READ,
        save=True
    )


def initialSetup():
    Setting = ModelImporter.model('setting')
    if Setting.get(constants.PluginSettings.DEMO_MODE, None) is None:
        Setting.set(constants.PluginSettings.DEMO_MODE, False)

    _provisionImages()
    _provisionSegmentationGroups()
    _provisionStudies()
    _provisionDefaultFeatureset()
