__author__ = 'stonerri'

from girder.constants import TerminalColor, AccessType
from girder.utility.model_importer import ModelImporter
from model_utility import *


def initialSetup():
    '''

    what does the girder configuration look like when all is said and done

    UDA study phase 1

    3 user groups, each with an example user

    Phase I - Initial reviewers
    udanovice -> udanovice

    Phase I - Trained reviewers
    udamike -> udamike

    Phase I - Expert reviewers
    udaexpert -> udaexpert


    3 collections for phase I

    Phase Ia -> initial markup

    Phase Ib -> initial review

    Phase Ic -> final review

    Phase Id -> complete images

    :return:
    '''

    m = ModelImporter()

    # create users if needed



    # the admin user
    uda_user = makeUserIfNotPresent('udastudy', 'udastudy', 'uda admin', 'testuser', 'admin@uda2study.org')
    uda_user['admin'] = True
    m.model('user').save(uda_user)



    # the user that uploads images & metadata
    uda_steve = makeUserIfNotPresent('udasteve', 'udasteve', 'uda steve', 'testuser', 'steve@uda2study.org')

    # create groups and add users
    phase0_group = makeGroupIfNotPresent('Phase 0', uda_user, 'These users are responsible for uploading raw images & metadata, and doing initial QC')
    m.model('group').addUser(phase0_group, uda_steve)
    m.model('group').updateGroup(phase0_group)

    phase0_collection =  makeCollectionIfNotPresent('Phase 0', uda_user, 'Images to QC')
    m.model('collection').setGroupAccess(phase0_collection, phase0_group, AccessType.ADMIN, save=True)

    # todo: fix this workaround in girder (needed for upload support into folders within collection)
    m.model('collection').setUserAccess(phase0_collection, uda_steve, AccessType.ADMIN, save=True)

    dropzipfolder = makeFolderIfNotPresent(phase0_collection, 'dropzip', 'upload zip folder of images here', 'collection', False, uda_user)
    dropcsv = makeFolderIfNotPresent(phase0_collection, 'dropcsv', 'upload image metadata as csv here', 'collection', False, uda_user)
    phase0_flagged_images = makeFolderIfNotPresent(phase0_collection, 'flagged', '', 'collection', False, uda_user)

    folders = [dropzipfolder, dropcsv, phase0_flagged_images]

    for folder in folders:
        m.model('folder').setUserAccess(folder, uda_steve, AccessType.ADMIN, save=True)




    # reviewers
    uda_novice = makeUserIfNotPresent('udanovice', 'udanovice', 'uda novice', 'testuser', 'novice@uda2study.org')
    uda_mike = makeUserIfNotPresent('udamike', 'udamike', 'uda trained', 'testuser', 'trained@uda2study.org')
    uda_expert = makeUserIfNotPresent('udaexpert', 'udaexpert', 'uda expert', 'testuser', 'expert@uda2study.org')


    phase1a_group = makeGroupIfNotPresent('Phase 1a', uda_user, 'These users are responsible for setting the normal and lesion boundaries, as well as defining the paint-by-number threshold.')
    m.model('group').addUser(phase1a_group, uda_novice)
    m.model('group').updateGroup(phase1a_group)

    phase1b_group = makeGroupIfNotPresent('Phase 1b', uda_user, 'These users are responsible for first pass review and editing of boundaries if necessary')
    m.model('group').addUser(phase1b_group, uda_mike)
    m.model('group').updateGroup(phase1b_group)

    phase1c_group = makeGroupIfNotPresent('Phase 1c', uda_user, 'These uses are responsible for signing off on the final series')
    m.model('group').addUser(phase1c_group, uda_expert)
    m.model('group').updateGroup(phase1c_group)

    phase2_group = makeGroupIfNotPresent('Phase 2', uda_user, 'Per feature annotation')
    m.model('group').addUser(phase2_group, uda_user)
    m.model('group').updateGroup(phase2_group)

    # create collections and assign group read permissions


    # only steve (or equivalent) can write to it
    # setUserAccess(self, doc, user, level, save=False):



    # everyone in phase 1 can read phase 0 content
    m.model('collection').setGroupAccess(phase0_collection, phase0_group, AccessType.ADMIN, save=True)
    m.model('collection').setGroupAccess(phase0_collection, phase1a_group, AccessType.READ, save=True)
    m.model('collection').setGroupAccess(phase0_collection, phase1b_group, AccessType.READ, save=True)
    m.model('collection').setGroupAccess(phase0_collection, phase1c_group, AccessType.READ, save=True)





    phase1a_collection = makeCollectionIfNotPresent('Phase 1a', uda_user, 'Images that have passed initial QC review')
    # phase1a_images = makeFolderIfNotPresent(phase1a_collection, 'images', '', 'collection', False, uda_user)

    m.model('collection').setGroupAccess(phase1a_collection, phase0_group, AccessType.READ, save=True)
    m.model('collection').setGroupAccess(phase1a_collection, phase1a_group, AccessType.READ, save=True)
    m.model('collection').setGroupAccess(phase1a_collection, phase1b_group, AccessType.READ, save=True)
    m.model('collection').setGroupAccess(phase1a_collection, phase1c_group, AccessType.READ, save=True)

    phase1b_collection = makeCollectionIfNotPresent('Phase 1b', uda_user, 'Images that have passed novice review')
    m.model('collection').setGroupAccess(phase1b_collection, phase0_group, AccessType.READ, save=True)
    m.model('collection').setGroupAccess(phase1b_collection, phase1a_group, AccessType.READ, save=True)
    m.model('collection').setGroupAccess(phase1b_collection, phase1b_group, AccessType.READ, save=True)
    m.model('collection').setGroupAccess(phase1b_collection, phase1c_group, AccessType.READ, save=True)


    phase1c_collection = makeCollectionIfNotPresent('Phase 1c', uda_user, 'Images that have passed trained review')
    m.model('collection').setGroupAccess(phase1c_collection, phase0_group, AccessType.READ, save=True)
    m.model('collection').setGroupAccess(phase1c_collection, phase1a_group, AccessType.READ, save=True)
    m.model('collection').setGroupAccess(phase1c_collection, phase1b_group, AccessType.READ, save=True)
    m.model('collection').setGroupAccess(phase1c_collection, phase1c_group, AccessType.READ, save=True)


    phase2_collection = makeCollectionIfNotPresent('Phase 2', uda_user, 'Images that have completed Phase 1')
    m.model('collection').setGroupAccess(phase2_collection, phase0_group, AccessType.READ, save=True)
    m.model('collection').setGroupAccess(phase2_collection, phase1a_group, AccessType.READ, save=True)
    m.model('collection').setGroupAccess(phase2_collection, phase1b_group, AccessType.READ, save=True)
    m.model('collection').setGroupAccess(phase2_collection, phase1c_group, AccessType.READ, save=True)
    m.model('collection').setGroupAccess(phase2_collection, phase2_group,  AccessType.READ, save=True)

