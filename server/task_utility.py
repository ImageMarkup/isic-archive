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


import datetime

import cherrypy

from girder.api import access
from girder.api.rest import Resource, RestException, loadmodel
from girder.api.describe import Description, describeRoute
from girder.constants import AccessType, SortDir

from .provision_utility import getAdminUser


class UDAResource(Resource):
    def __init__(self):
        super(UDAResource, self).__init__()
        self.resourceName = 'uda'

        self.route('GET', ('task', 'qc'), self.p0TaskList)
        self.route('POST', ('task', 'qc', ':folder_id', 'complete'),
                   self.p0TaskComplete)

        self.route('POST', ('task', 'select', ':folder_id'),
                   self.selectTaskComplete)

    @describeRoute(
        Description('DEPRECATED: Complete a select task')
    )
    @access.user
    @loadmodel(map={'folder_id': 'folder'}, model='folder',
               level=AccessType.READ)
    def selectTaskComplete(self, folder, params):
        contents = self.getBodyJson()

        flagged_image_items = [
            self.model('item').load(image_item_id, force=True)
            for image_item_id in contents['flagged']
        ]
        for image_item in flagged_image_items:
            if image_item['folderId'] != folder['_id']:
                raise RestException(
                    'Flagged image %s is not inside folder %s' %
                    (image_item['_id'], folder['_id']))
        good_image_items = [
            self.model('item').load(image_item_id, force=True)
            for image_item_id in contents['good']
        ]
        for image_item in good_image_items:
            if image_item['folderId'] != folder['_id']:
                raise RestException(
                    'Good image %s is not inside folder %s' %
                    (image_item['_id'], folder['_id']))

        parent_type = folder['parentCollection']
        parent_entity = self.model(parent_type).load(
            folder['parentId'], force=True)

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

    @describeRoute(
        Description('List available tasks.')
        .errorResponse()
    )
    @access.user
    def p0TaskList(self, params):
        Collection = self.model('collection')
        Folder = self.model('folder')
        User = self.model('user', 'isic_archive')

        User.requireReviewDataset(self.getCurrentUser())

        prereviewCollection = Collection.findOne({'name': 'Pre-review Images'})
        results = [
            {
                'dataset': {
                    '_id': folder['_id'],
                    'name': folder['name']
                },
                'count': Folder.childItems(
                    folder,
                    filters={'meta.originalFilename': {'$exists': True}}
                    ).count(),
            }
            for folder in self.model('folder').find(
                {'parentId': prereviewCollection['_id']},
                sort=[('lowerName', SortDir.ASCENDING)])
        ]
        results = [result for result in results if result['count']]
        return results

    @describeRoute(
        Description('Complete a QC review task.')
        .param('details', 'JSON details of images to be QC\'d.',
               paramType='body')
        .errorResponse()
    )
    @access.user
    @loadmodel(map={'folder_id': 'folder'}, model='folder',
               level=AccessType.READ)
    def p0TaskComplete(self, folder, params):
        Collection = self.model('collection')
        Folder = self.model('folder')
        Item = self.model('item')

        # verify user's access to folder and phase
        prereviewCollection = Collection.findOne({'name': 'Pre-review Images'})
        Collection.requireAccess(
            prereviewCollection, self.getCurrentUser(), AccessType.READ)
        if folder['baseParentId'] != prereviewCollection['_id']:
            raise RestException(
                'Folder %s is not inside Pre-review Images' % folder['_id'])

        contents = self.getBodyJson()

        # verify that all images are in folder
        flagged_image_items = [
            Item.load(image_item_id, force=True)
            for image_item_id in contents['flagged']
        ]
        for image_item in flagged_image_items:
            if image_item['folderId'] != folder['_id']:
                raise RestException(
                    'Flagged image %s is not inside folder %s' %
                    (image_item['_id'], folder['_id']))
        good_image_items = [
            Item.load(image_item_id, force=True)
            for image_item_id in contents['good']
        ]
        for image_item in good_image_items:
            if image_item['folderId'] != folder['_id']:
                raise RestException(
                    'Good image %s is not inside folder %s' %
                    (image_item['_id'], folder['_id']))

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
        images_collection = Collection.findOne({'name': 'Lesion Images'})

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


class TaskHandler(Resource):
    def __init__(self):
        super(TaskHandler, self).__init__()
        self.resourceName = 'task'

        self.route('GET', ('p0', ':folder_id'), self.p0TaskRedirect)

    @describeRoute(
        Description('Redirect to a QC review task')
    )
    @access.cookie
    @access.user
    @loadmodel(map={'folder_id': 'folder'}, model='folder',
               level=AccessType.READ)
    def p0TaskRedirect(self, folder, params):
        Collection = self.model('collection')
        Folder = self.model('folder')

        prereviewCollection = Collection.findOne({
            'name': 'Pre-review Images'})
        if folder['baseParentId'] != prereviewCollection['_id']:
            raise RestException(
                'Folder "%s" is not in collection "Pre-review Images"' %
                folder['_id'])

        if not Folder.childItems(
                folder,
                filters={'meta.originalFilename': {'$exists': True}}
                ).count():
            raise RestException(
                'Folder "%s" in collection "Pre-review Images" is empty' %
                folder['_id'])

        redirect_url = '/uda/gallery#/qc/%s' % folder['_id']
        raise cherrypy.HTTPRedirect(redirect_url, status=307)
