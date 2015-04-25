#!/usr/bin/env python
# -*- coding: utf-8 -*-

from girder.constants import AccessType
from girder.utility.model_importer import ModelImporter


def onUserCreated(event):
    if ModelImporter.model('setting').get('uda.demo_mode', None):
        user = event.info
        addUserToAllUDAGroups(user)


def addUserToAllUDAGroups(user):
    # group should already exist
    for phase in ['Phase 0', 'Phase 1a', 'Phase 1b', 'Phase 1c', 'Phase 2']:
        group = getOrCreateUDAGroup(name=phase, description=None, public=None)
        ModelImporter.model('group').addUser(
            group=group,
            user=user,
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


def getOrCreateUDAGroup(name, description, public):
    group = ModelImporter.model('group').findOne({'name': name})
    if not group:
        group = ModelImporter.model('group').createGroup(
            name=name,
            creator=getAdminUser(),
            description=description,
            public=public
        )
        # remove udaadmin from group
    return group


def getOrCreateUDACollection(name, description, public):
    collection = ModelImporter.model('collection').findOne(
        {'name': name})
    if not collection:
        collection = ModelImporter.model('collection').createCollection(
            name=name,
            creator=getAdminUser(),
            description=description,
            public=public
        )
        # delete default folders
        for folder in ModelImporter.model('folder').find(
                {'parentId': collection['_id']}):
            ModelImporter.model('folder').remove(folder)
    return collection


def getOrCreateUDAFolder(name, description, parent, parent_type):
    folder = ModelImporter.model('folder').findOne({
        'name': name,
        'parentId': parent['_id']
    })
    if not folder:
        folder = ModelImporter.model('folder').createFolder(
            parent=parent,
            name=name,
            description=description,
            parentType=parent_type,
            public=None,
            creator=getAdminUser()
        )
        if parent_type != 'folder':
            # Girder doesn't inherit access from parent collections, but we will
            ModelImporter.model('folder').copyAccessPolicies(
                src=parent,
                dest=folder,
                save=True
            )
    return folder


def setupUdaPhase(phase_name, collection_description, group_description):
    collection = getOrCreateUDACollection(
        name=phase_name,
        description=collection_description,
        public=False
    )
    group = getOrCreateUDAGroup(
        name=phase_name,
        description=group_description,
        public=True
    )
    ModelImporter.model('collection').setGroupAccess(
        doc=collection,
        group=group,
        level=AccessType.READ,
        save=True
    )
    return collection, group


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
    # group should already exist
    group = getOrCreateUDAGroup(name=phase, description=None, public=None)
    ModelImporter.model('group').addUser(
        group=group,
        user=test_user,
        level=AccessType.READ
    )


def initialSetup():
    phase0_collection, phase0_group = setupUdaPhase(
        phase_name='Phase 0',
        collection_description='Images to QC',
        group_description='Users responsible for uploading raw images & metadata, and doing initial QC'
    )
    dropzip_folder = getOrCreateUDAFolder(
        name='dropzip',
        description='Upload zipped folders of images here',
        parent=phase0_collection,
        parent_type='collection'
    )
    ModelImporter.model('folder').setGroupAccess(
        doc=dropzip_folder,
        group=phase0_group,
        level=AccessType.WRITE,
        save=True
    )
    getOrCreateUDAFolder(
        name='flagged',
        description='Images flagged during Phase 0 are here',
        parent=phase0_collection,
        parent_type='collection'
    )

    setupUdaPhase(
        phase_name='Phase 1a',
        collection_description='Images that have passed initial QC review',
        group_description='Users responsible for setting the normal and lesion boundaries, as well as defining the paint-by-number threshold'
    )
    setupUdaPhase(
        phase_name='Phase 1b',
        collection_description='Images that have passed novice review',
        group_description='Users responsible for first pass review and editing of boundaries if necessary'
    )
    setupUdaPhase(
        phase_name='Phase 1c',
        collection_description='Images that have passed trained review',
        group_description='Users responsible for signing off on the final series'
    )
    setupUdaPhase(
        phase_name='Phase 2',
        collection_description='Images that have completed Phase 1',
        group_description='Users creating feature annotations'
    )
    getOrCreateUDACollection('Complete',
                             description='Images that have been fully annotated',
                             public=True
    )

    MAKE_TEST_USERS = False
    if MAKE_TEST_USERS:
        setupUdaTestUser(
            phase='Phase 0',
            username='udauploader',
            password='udauploader',
            label='Uploader',
        )
        setupUdaTestUser(
            phase='Phase 1a',
            username='udanovice',
            password='udanovice',
            label='Novice',
        )
        setupUdaTestUser(
            phase='Phase 1b',
            username='udatrained',
            password='udatrained',
            label='Trained',
        )
        setupUdaTestUser(
            phase='Phase 1c',
            username='udaexpert',
            password='udaexpert',
            label='Expert',
        )
        setupUdaTestUser(
            phase='Phase 2',
            username='udaannotator',
            password='udaannotator',
            label='Annotator',
        )
