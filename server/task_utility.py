#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime

import cherrypy

from girder.api import access
from girder.api.rest import Resource, RestException, loadmodel
from girder.api.describe import Description
from girder.constants import AccessType, SortDir
from girder.models.model_base import AccessException
from girder.utility.model_importer import ModelImporter

from .provision_utility import getAdminUser


def getItemsInFolder(folder):
    return list(ModelImporter.model('folder').childItems(
        folder,
        filters={'meta.originalFilename': {'$exists': True}}
    ))


class UDAResource(Resource):
    def __init__(self):
        super(UDAResource, self).__init__()
        self.resourceName = 'uda'

        self.route('GET', ('task', 'qc'), self.p0TaskList)
        self.route('POST', ('task', 'qc', ':folder_id', 'complete'), self.p0TaskComplete)

        self.route('POST', ('task', 'select', ':folder_id'), self.selectTaskComplete)

    @access.user
    @loadmodel(map={'folder_id': 'folder'}, model='folder', level=AccessType.READ)
    def selectTaskComplete(self, folder, params):
        contents = self.getBodyJson()

        flagged_image_items = [
            self.model('item').load(image_item_id, force=True)
            for image_item_id in contents['flagged']
        ]
        for image_item in flagged_image_items:
            if image_item['folderId'] != folder['_id']:
                raise RestException('Flagged image %s is not inside folder %s' % (image_item['_id'], folder['_id']))
        good_image_items = [
            self.model('item').load(image_item_id, force=True)
            for image_item_id in contents['good']
        ]
        for image_item in good_image_items:
            if image_item['folderId'] != folder['_id']:
                raise RestException('Good image %s is not inside folder %s' % (image_item['_id'], folder['_id']))

        parent_type = folder['parentCollection']
        parent_entity = self.model(parent_type).load(folder['parentId'], force=True)

        flagged_folder = self.model('folder').createFolder(
            reuseExisting=True,
            name='%s (flagged)' % folder['name'],
            parent=parent_entity,
            parentType=parent_type,
            creator=self.getCurrentUser()
        )
        for image_item in flagged_image_items:
            self.model('item').move(image_item, flagged_folder)

        accepted_folder = self.model('folder').createFolder(
            reuseExisting=True,
            name='%s (accepted)' % folder['name'],
            parent=parent_entity,
            parentType=parent_type,
            creator=self.getCurrentUser()
        )
        for image_item in good_image_items:
            self.model('item').move(image_item, accepted_folder)

        return {'status': 'success'}


    def _requireCollectionAccess(self, collection_name):
        assert(collection_name in ('Phase 0',))

        collection = self.model('collection').findOne({'name': collection_name})
        group = self.model('group').findOne({'name': collection_name})
        user = self.getCurrentUser()

        self.model('collection').requireAccess(collection, user, AccessType.READ)
        if group['_id'] not in user.get('groups', []):
            raise AccessException('access denied for user %s to group %s' % (user['_id'], collection_name))

        return collection


    @access.user
    def p0TaskList(self, params):
        try:
            collection = self._requireCollectionAccess('Phase 0')
        except AccessException:
            return []
        results = [
            {
                'dataset': {
                    '_id': folder['_id'],
                    'name': folder['name']
                },
                'count': len(getItemsInFolder(folder)),
            }
            for folder in self.model('folder').find({
                'parentId': collection['_id'],
                'name': {'$ne': 'dropzip'}
            }, sort=[('lowerName', SortDir.ASCENDING)])
        ]
        results = [result for result in results if result['count']]
        return results

    p0TaskList.description = (
        Description('List available tasks.')
        .responseClass('UDA')
        .errorResponse())


    @access.user
    @loadmodel(map={'folder_id': 'folder'}, model='folder', level=AccessType.READ)
    def p0TaskComplete(self, folder, params):
        Folder = self.model('folder')
        Item = self.model('item')

        # verify user's access to folder and phase
        phase0_collection = self.model('collection').findOne({'name': 'Phase 0'})
        self.model('collection').requireAccess(phase0_collection, self.getCurrentUser(), AccessType.READ)
        if folder['baseParentId'] != phase0_collection['_id']:
            raise RestException('Folder %s is not inside Phase 0' % folder['_id'])

        contents = self.getBodyJson()

        # verify that all images are in folder
        flagged_image_items = [
            Item.load(image_item_id, force=True)
            for image_item_id in contents['flagged']
        ]
        for image_item in flagged_image_items:
            if image_item['folderId'] != folder['_id']:
                raise RestException('Flagged image %s is not inside folder %s' % (image_item['_id'], folder['_id']))
        good_image_items = [
            Item.load(image_item_id, force=True)
            for image_item_id in contents['good']
        ]
        for image_item in good_image_items:
            if image_item['folderId'] != folder['_id']:
                raise RestException('Good image %s is not inside folder %s' % (image_item['_id'], folder['_id']))

        # move flagged images into flagged folder
        self.model('image', 'isic_archive').flagMultiple(
            images=flagged_image_items,
            reason='phase0',
            user=self.getCurrentUser()
        )
        # TODO: move metadata:
        #  'qc_user' to 'flaggedUserId'
        #  'qc_result' to 'flaggedReason'
        #  create 'flaggedTime'

        # move good images into Lesion Images folder
        images_collection = self.model('collection').findOne({'name': 'Lesion Images'})

        images_dataset_folder = Folder.createFolder(
            parent=images_collection,
            name=folder['name'],
            description=folder['description'],
            parentType='collection',
            public=None,
            creator=getAdminUser(),
            allowRename=False,
            reuseExisting=True
        )
        if not images_dataset_folder.get('meta'):
            images_dataset_folder = Folder.setMetadata(
                images_dataset_folder, folder.get('meta', {}))

        for image_item in good_image_items:
            qc_metadata = {
                'qc_user': self.getCurrentUser()['_id'],
                'qc_result': 'ok',
                'qc_stop_time': datetime.datetime.utcnow(),
            }
            Item.setMetadata(image_item, qc_metadata)
            Item.move(image_item, images_dataset_folder)

        # remove empty folders in original collection
        if Folder.subtreeCount(folder) == 1:
            Folder.remove(folder)

        return {'status': 'success'}

    p0TaskComplete.description = (
        Description('Complete a Phase 0 (qc) task.')
        .responseClass('UDA')
        .param('details', 'JSON details of images to be QC\'d.', paramType='body')
        .errorResponse())


class TaskHandler(Resource):
    def __init__(self):
        super(TaskHandler, self).__init__()
        self.resourceName = 'task'

        self.route('GET', ('p0', ':folder_id'), self.p0TaskRedirect)


    @access.cookie
    @access.user
    @loadmodel(map={'folder_id': 'folder'}, model='folder', level=AccessType.READ)
    def p0TaskRedirect(self, folder, params):
        collection = self.model('collection').findOne({'name': 'Phase 0'})
        if folder['baseParentId'] != collection['_id']:
            raise RestException('Folder "%s" is not in collection "Phase 0"' % folder['_id'])

        items = getItemsInFolder(folder)
        if not items:
            raise RestException('Folder "%s" in collection "Phase 0" is empty' % folder['_id'])

        redirect_url = '/uda/gallery#/qc/%s' % folder['_id']
        raise cherrypy.HTTPRedirect(redirect_url, status=307)
