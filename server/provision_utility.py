#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
import json
import os

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

    if ModelImporter.model('setting').get(constants.PluginSettings.DEMO_MODE):
        addUserToAllUDAGroups(user)


def addUserToAllUDAGroups(user):
    # group should already exist
    for collection in [
        ISIC.Phase0,
        ISIC.LesionImages,
        ISIC.AnnotationStudies,
    ]:
        if collection.group:
            ModelImporter.model('group').addUser(
                group=collection.group,
                user=user,
                # TODO: change
                level=AccessType.READ
            )


def getOrCreateUDAUser(username, password,
                       first_name, last_name, email,
                       admin, public):
    user = ModelImporter.model('user').findOne({'login': username})
    if not user:
        user = ModelImporter.model('user').createUser(
            login=username,
            password=password,
            firstName=first_name,
            lastName=last_name,
            email=email,
            admin=admin,
            public=public
        )
        # delete default folders
        for folder in ModelImporter.model('folder').find(
                {'parentId': user['_id']}):
            ModelImporter.model('folder').remove(folder)
    return user


def getAdminUser():
    # TODO: cache this?
    return getOrCreateUDAUser(
        username='udastudy',
        password='udastudy',
        first_name='UDA Study',
        last_name='Admin',
        email='admin@uda2study.org',
        admin=True,
        public=False
    )


class _ISICCollection(ModelImporter):
    # TODO: add a refresh mechanism, or just store the ids, rather than the whole model
    def __init__(self,
            collection_name, collection_description,
            public,
            group_name=None, group_description=None):

        self.collection = self.model('collection').findOne(
            {'name': collection_name})
        if not self.collection:
            self.collection = self.model('collection').createCollection(
                name=collection_name,
                creator=getAdminUser(),
                description=collection_description,
                public=public
            )

        if group_name:
            self.group = self.model('group').findOne(
                {'name': group_name})
            if not self.group:
                self.group = self.model('group').createGroup(
                    name=group_name,
                    creator=getAdminUser(),
                    description=group_description,
                    public=True
                )
                self.model('group').removeUser(self.group, getAdminUser())
                # remove udaadmin from group

                self.model('collection').setGroupAccess(
                    doc=self.collection,
                    group=self.group,
                    # TODO: make this a special access level
                    level=AccessType.READ,
                    save=True
                )
        else:
            self.group = None

    @classmethod
    def createFolder(cls, name, description, parent, parent_type):
        return cls.model('folder').createFolder(
            parent=parent,
            name=name,
            description=description,
            parentType=parent_type,
            public=None,
            creator=getAdminUser(),
            allowRename=False,
            reuseExisting=True
        )


# this will be populated in 'initialSetup'
class ISIC(object):
    Phase0 = None
    LesionImages = None
    AnnotationStudies = None


def setupUdaTestUser(phase, username, password, label):
    assert(' ' not in label)
    test_user = getOrCreateUDAUser(
        username=username,
        password=password,
        first_name='UDA Study',
        last_name=label,
        email='%s@uda2study.org' % label.lower(),
        admin=False,
        public=False
    )
    ModelImporter.model('group').addUser(
        group=phase.group,
        user=test_user,
        level=AccessType.READ
    )


def initialSetup(info):
    Group = ModelImporter.model('group')

    if ModelImporter.model('setting').get(constants.PluginSettings.DEMO_MODE, None) is None:
        ModelImporter.model('setting').set(constants.PluginSettings.DEMO_MODE, False)

    ISIC.Phase0 = _ISICCollection(
        collection_name='Phase 0',
        collection_description='Images to QC',
        public=False,
        group_name='Phase 0',
        group_description='Users responsible for doing initial QC'
    )

    # Create empty "dataset contributors" group
    if not Group.findOne(
        {'name': 'Dataset Contributors'}):
        contributorsGroup = Group.createGroup(
            name='Dataset Contributors',
            creator=getAdminUser(),
            description='Users that can create datasets',
            public=True
        )
        Group.removeUser(contributorsGroup, getAdminUser())

    ISIC.Flagged = _ISICCollection(
        collection_name='Flagged Images',
        collection_description='Images that have been flagged for any reason',
        public=False
    )

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

    ISIC.LesionImages = _ISICCollection(
        collection_name='Lesion Images',
        collection_description='Lesion images available for annotation studies',
        public=True
    )

    ISIC.AnnotationStudies = _ISICCollection(
        collection_name='Annotation Studies',
        collection_description='Clinical feature annotation studies',
        public=True,
        group_name='Study Administrators',
        group_description='Annotation study creators and administrators'
    )

    for featureset_file_name in [
        'uda2study.json',
        'isic_analytical.json',
        'isic_conventional.json'
    ]:
        featureset_file_path = os.path.join(info['pluginRootDir'], 'custom', 'config', featureset_file_name)
        with open(featureset_file_path, 'r') as featureset_file:
            featureset_data = json.load(featureset_file)
            featureset = ModelImporter.model('featureset', 'isic_archive').findOne(
                {'name': featureset_data['name']})
            if not featureset:
                # these values may be updated to be more accurate
                featureset_data['creatorId'] = getAdminUser()['_id']
                featureset_data['created'] = datetime.datetime.utcnow()
                ModelImporter.model('featureset', 'isic_archive').save(featureset_data)

    MAKE_TEST_USERS = False
    if MAKE_TEST_USERS:
        setupUdaTestUser(
            phase=ISIC.Phase0,
            username='udauploader',
            password='udauploader',
            label='Uploader',
        )
        setupUdaTestUser(
            phase=ISIC.AnnotationStudies,
            username='udaannotator',
            password='udaannotator',
            label='Annotator',
        )
