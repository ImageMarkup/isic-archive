

from girder import events
from girder.constants import TerminalColor, AccessType
from girder.utility.model_importer import ModelImporter

from pprint import pprint as pp
import zipfile
import mimetypes

from hashlib import sha512
import os
import tempfile
import stat


# what does the girder configuration look like when all is said and done

    # UDA study phase 1
    #
    # 3 user groups, each with an example user

    # Phase I - Initial reviewers
    # udanovice -> udanovice

    # Phase I - Trained reviewers
    # udamike -> udamike

    # Phase I - Expert reviewers
    # udaexpert -> udaexpert


    # 3 collections for phase I

    # Phase Ia -> initial markup

    # Phase Ib -> initial review

    # Phase Ic -> final review

    # Phase Id -> complete images


    # def createUser(self, login, password, firstName, lastName, email,
    #                admin=False, public=True):
def makeUserIfNotPresent(username, password, firstName, lastName, email):

    m = ModelImporter()

    user_query = m.model('user').find({'firstName' : firstName})

    user = None

    if user_query.count() == 0:
        # user doens't exist, create
        user = m.model('user').createUser(username, password, firstName, lastName, email)

    elif user_query.count() == 1:
        user = user_query[0]

    else:
        print TerminalColor.error('More than one user with same first name, returning first')
        user = user_query[0]

    return user



def makeFolderIfNotPresent(collection, folderName, folderDescription, parentType, public, creator):

    m = ModelImporter()

    folder_query = m.model('folder').find(
        { '$and' : [
            {'parentId': collection['_id']},
            {'name': folderName}
        ]})

    folder = None

    if folder_query.count() == 0:

        folder = m.model('folder').createFolder(collection, folderName, folderDescription, parentType=parentType, public=public, creator=creator)

    else:

        folder = folder_query[0]



    return folder



def makeGroupIfNotPresent(groupName, creator, description):

    m = ModelImporter()

    group_query = m.model('group').find({'name' : groupName})
    group = None

    if group_query.count() == 0:
        group = m.model('group').createGroup(groupName, creator, description)

    elif group_query.count() == 1:
        group = group_query[0]

    else:
        print TerminalColor.error('More than one group with this name, returning first')
        group = group_query[0]

    return group


def makeCollectionIfNotPresent(collectionName, creator, description):

    m = ModelImporter()

    collection_query = m.model('collection').find({'name' : collectionName})
    collection = None

    if collection_query.count() == 0:
        collection = m.model('collection').createCollection(collectionName, creator, description, public=False)

    elif collection_query.count() == 1:
        collection = collection_query[0]

    else:
        print TerminalColor.error('More than one collection with this name, returning first')
        collection = collection_query[0]

    return collection




# zip file upload of packed images

def load(info):

    m = ModelImporter()

    # create users if needed

    # the admin user
    uda_user = makeUserIfNotPresent('udastudy', 'udastudy', 'uda admin', 'testuser', 'admin@uda2study.org')

    # the user that uploads images & metadata
    uda_steve = makeUserIfNotPresent('udasteve', 'udasteve', 'uda steve', 'testuser', 'steve@uda2study.org')

    # reviewers
    uda_novice = makeUserIfNotPresent('udanovice', 'udanovice', 'uda novice', 'testuser', 'novice@uda2study.org')
    uda_mike = makeUserIfNotPresent('udamike', 'udamike', 'uda trained', 'testuser', 'trained@uda2study.org')
    uda_expert = makeUserIfNotPresent('udaexpert', 'udaexpert', 'uda expert', 'testuser', 'expert@uda2study.org')

    # create groups and add users
    phase0_group = makeGroupIfNotPresent('Phase 0', uda_user, 'These users are responsible for setting the normal and lesion boundaries, as well as defining the paint-by-number threshold.')
    m.model('group').addUser(phase0_group, uda_steve)
    m.model('group').updateGroup(phase0_group)


    phase1a_group = makeGroupIfNotPresent('Phase 1a', uda_user, 'These users are responsible for setting the normal and lesion boundaries, as well as defining the paint-by-number threshold.')
    m.model('group').addUser(phase1a_group, uda_novice)
    m.model('group').updateGroup(phase1a_group)

    phase1b_group = makeGroupIfNotPresent('Phase 1b', uda_user, 'These users are responsible for first pass review and editing of boundaries if necessary')
    m.model('group').addUser(phase1b_group, uda_mike)
    m.model('group').updateGroup(phase1b_group)

    phase1c_group = makeGroupIfNotPresent('Phase 1c', uda_user, 'These uses are responsible for signing off on the final series')
    m.model('group').addUser(phase1c_group, uda_expert)
    m.model('group').updateGroup(phase1c_group)

    # create collections and assign group read permissions


    phase0_collection =  makeCollectionIfNotPresent('Phase 0', uda_user, 'Images to QC')
    phase0_images = makeFolderIfNotPresent(phase0_collection, 'images', '', 'collection', False, uda_user)
    phase0_flagged_images = makeFolderIfNotPresent(phase0_collection, 'flagged', '', 'collection', False, uda_user)

    m.model('collection').setGroupAccess(phase0_collection, phase1a_group, AccessType.READ, save=True)
    m.model('collection').setGroupAccess(phase0_collection, phase1b_group, AccessType.READ, save=True)
    m.model('collection').setGroupAccess(phase0_collection, phase1c_group, AccessType.READ, save=True)

    # give steve write access
    m.model('collection').setGroupAccess(phase0_collection, phase0_group, AccessType.WRITE, save=True)

    phase1a_collection = makeCollectionIfNotPresent('Phase 1a', uda_user, 'Images that have passed initial QC review')
    m.model('collection').setGroupAccess(phase1a_collection, phase1a_group, AccessType.READ, save=True)
    m.model('collection').setGroupAccess(phase1a_collection, phase1b_group, AccessType.READ, save=True)
    m.model('collection').setGroupAccess(phase1a_collection, phase1c_group, AccessType.READ, save=True)

    phase1b_collection = makeCollectionIfNotPresent('Phase 1b', uda_user, 'Images that have passed novice review')
    m.model('collection').setGroupAccess(phase1b_collection, phase1a_group, AccessType.READ, save=True)
    m.model('collection').setGroupAccess(phase1b_collection, phase1b_group, AccessType.READ, save=True)
    m.model('collection').setGroupAccess(phase1b_collection, phase1c_group, AccessType.READ, save=True)

    phase1c_collection = makeCollectionIfNotPresent('Phase 1c', uda_user, 'Images that have passed trained review')
    m.model('collection').setGroupAccess(phase1c_collection, phase1a_group, AccessType.READ, save=True)
    m.model('collection').setGroupAccess(phase1c_collection, phase1b_group, AccessType.READ, save=True)
    m.model('collection').setGroupAccess(phase1c_collection, phase1c_group, AccessType.READ, save=True)

    phase1d_collection = makeCollectionIfNotPresent('Phase 1d', uda_user, 'Images that have completed Phase 1')
    m.model('collection').setGroupAccess(phase1d_collection, phase1a_group, AccessType.READ, save=True)
    m.model('collection').setGroupAccess(phase1d_collection, phase1b_group, AccessType.READ, save=True)
    m.model('collection').setGroupAccess(phase1d_collection, phase1c_group, AccessType.READ, save=True)


