#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
import json
import operator
import os
import random

import cherrypy
import pymongo

from girder.api import access
from girder.api.rest import Resource, RestException, loadmodel
from girder.api.describe import Description
from girder.constants import AccessType
from girder.models.model_base import AccessException
from girder.utility.model_importer import ModelImporter

from .provision_utility import _ISICCollection


def getItemsInFolder(folder):
    return list(ModelImporter.model('folder').childItems(
        folder,
        filters={'meta.originalFilename': {'$exists': True}}
    ))


class UDAResource(Resource):
    def __init__(self, plugin_root_dir):
        super(UDAResource, self).__init__()
        self.resourceName = 'uda'
        self.plugin_root_dir = plugin_root_dir

        self.route('GET', ('task',), self.taskList)
        self.route('POST', ('task', 'qc', ':folder_id', 'complete'), self.p0TaskComplete)
        self.route('GET', ('task', 'markup', ':item_id'), self.p1TaskDetail)

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
        assert(collection_name in ('Phase 0', 'Phase 1a', 'Phase 1b'))

        collection = self.model('collection').findOne({'name': collection_name})
        group = self.model('group').findOne({'name': collection_name})
        user = self.getCurrentUser()

        self.model('collection').requireAccess(collection, user, AccessType.READ)
        if group['_id'] not in user.get('groups', []):
            raise AccessException('access denied for user %s to group %s' % (user['_id'], collection_name))

        return collection


    @access.user
    def taskList(self, params):
        result = list()

        # TODO: make this a global constant somewhere
        PHASE_TASK_URLS = {
            'Phase 0': '/uda/task/p0/%(folder_id)s',
            'Phase 1a': '/uda/task/p1a/%(folder_id)s',
            'Phase 1b': '/uda/task/p1b/%(folder_id)s',
            'Phase 2': '/uda/task/p2/%(study_id)s'
        }
        for phase_name, task_url in sorted(PHASE_TASK_URLS.iteritems()):
            if phase_name != 'Phase 2':
                try:
                    collection = self._requireCollectionAccess(phase_name)
                except AccessException:
                    continue

                datasets = (
                    {
                        'name': folder['name'],
                        'count': len(getItemsInFolder(folder)),
                        'url': task_url % {'folder_id': folder['_id']}
                    }
                    for folder in self.model('folder').find({
                        'parentId': collection['_id'],
                        'name': {'$ne': 'dropzip'}
                    })
                )
            else:
                # TODO: this could be done more efficiently, without duplicate queries,
                #   but let's wait until this API refactored
                study_list = self.model('study', 'isic_archive').find(
                    annotator_user=self.getCurrentUser(),
                    state=self.model('study', 'isic_archive').State.ACTIVE
                )
                if not study_list.count():
                    continue
                datasets = (
                    {
                        'name': study['name'],
                        'count': self.model('study', 'isic_archive').childAnnotations(
                            study=study,
                            annotator_user=self.getCurrentUser(),
                            state=self.model('study', 'isic_archive').State.ACTIVE
                        ).count(),
                        'url': task_url % {'study_id': study['_id']}
                    }
                    for study in study_list
                )
                # TODO: replace this with the actual collection description,
                #   and update that to note Phase 2
                collection = {
                    'name': 'Annotation Studies',
                    'description': 'Clinical feature annotation studies (Phase 2)'
                }

            datasets = sorted(datasets, key=operator.itemgetter('name'))

            result.append({
                'name': collection['name'],
                'description': collection['description'],
                'count': sum(dataset['count'] for dataset in datasets),
                'datasets': datasets
            })

        return result

    taskList.description = (
        Description('List available tasks.')
        .responseClass('UDA')
        .errorResponse())


    @access.user
    @loadmodel(map={'folder_id': 'folder'}, model='folder', level=AccessType.READ)
    def p0TaskComplete(self, folder, params):
        # verify user's access to folder and phase
        phase0_collection = self.model('collection').findOne({'name': 'Phase 0'})
        self.model('collection').requireAccess(phase0_collection, self.getCurrentUser(), AccessType.READ)
        if folder['baseParentId'] != phase0_collection['_id']:
            raise RestException('Folder %s is not inside Phase 0' % folder['_id'])

        contents = self.getBodyJson()

        # verify that all images are in folder
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

        # move good images into phase 1a folder
        phase1a_collection = self.model('collection').findOne({'name': 'Phase 1a'})
        phase1a_images = _ISICCollection.createFolder(
            name=folder['name'],
            description=folder['description'],
            parent=phase1a_collection,
            parent_type='collection'
        )
        for image_item in good_image_items:
            qc_metadata = {
                'qc_user': self.getCurrentUser()['_id'],
                'qc_result': 'ok',
                'qc_stop_time': datetime.datetime.utcnow(),
            }
            self.model('item').setMetadata(image_item, qc_metadata)
            self.model('item').move(image_item, phase1a_images)

        # remove empty folders in original collection
        if self.model('folder').subtreeCount(folder) == 1:
            self.model('folder').remove(folder)

        return {'status': 'success'}

    p0TaskComplete.description = (
        Description('Complete a Phase 0 (qc) task.')
        .responseClass('UDA')
        .param('details', 'JSON details of images to be QC\'d.', paramType='body')
        .errorResponse())


    @access.user
    @loadmodel(map={'item_id': 'item'}, model='item', level=AccessType.READ)
    def p1TaskDetail(self, item, params):
        # verify item is in the correct phase and user has access
        collection = self.model('collection').load(
            id=item['baseParentId'],
            level=AccessType.READ,
            user=self.getCurrentUser()
        )
        phase_name = collection['name']
        if not (phase_name.startswith('Phase 1') or phase_name == 'Phase 2'):
            raise RestException('Item %s is not inside Phase 1 or Phase 2' % item['_id'])

        return_dict = {
            'phase': phase_name,
            'items': [item],
        }

        # if necessary, load annotations from previous phase
        if phase_name == 'Phase 1b':
            return_dict['loadAnnotation'] = True

            previous_phase_annotation_file_name_ending = '-%s.json' % 'p1a'
            for item_file in sorted(
                    self.model('item').childFiles(item),
                    key=operator.itemgetter('created'),
                    reverse=True
            ):
                if item_file['name'].endswith(previous_phase_annotation_file_name_ending):
                    item_file_generator = self.model('file').download(item_file, headers=False)
                    previous_phase_annotation = json.loads(''.join(item_file_generator()))
                    return_dict['annotation'] = previous_phase_annotation['p1a']['steps']
                    break
            else:
                # TODO: no file found, raise error
                pass

        else:
            return_dict['loadAnnotation'] = False

        # include static phase config
        phase_config_file_name = '%s.json' % phase_name.replace(' ', '').lower()
        phase_config_file_path = os.path.join(self.plugin_root_dir, 'custom', 'config', phase_config_file_name)
        with open(phase_config_file_path, 'r') as phase_config_file:
            return_dict['decision_tree'] = json.load(phase_config_file)

        return return_dict

    p1TaskDetail.description = (
        Description('Get details of a Phase 1 (markup) task.')
        .responseClass('UDA')
        .param('item_id', 'The item ID.', paramType='path')
        .errorResponse())


class TaskHandler(Resource):
    def __init__(self, plugin_root_dir):
        super(TaskHandler, self).__init__()
        self.resourceName = 'task'
        self.plugin_root_dir = plugin_root_dir

        self.route('GET', (), self.taskDashboard)
        self.route('GET', ('p0', ':folder_id'), self.p0TaskRedirect)
        self.route('GET', ('p1a', ':folder_id'), self.p1aTaskRedirect)
        self.route('GET', ('p1b', ':folder_id'), self.p1bTaskRedirect)
        self.route('GET', ('p2', ':study_id'), self.p2TaskRedirect)


    @access.cookie
    @access.public
    def taskDashboard(self, params):
        return cherrypy.lib.static.serve_file(os.path.join(self.plugin_root_dir, 'custom', 'task.html'))


    def _taskRedirect(self, phase_name, folder, url_format):
        collection = self.model('collection').findOne({'name': phase_name})
        if folder['baseParentId'] != collection['_id']:
            raise RestException('Folder "%s" is not in collection "%s"' % (folder['_id'], phase_name))

        items = getItemsInFolder(folder)
        if not items:
            raise RestException('Folder "%s" in collection "%s" is empty' % (folder['_id'], phase_name))

        # this will help slightly with multiple users simultaneously segmenting
        #   the same dataset, but still has a race condition for smaller datasets
        task_item = random.choice(items)

        redirect_url = url_format % {
            'folder_id': folder['_id'],
            'item_id': task_item['_id']
        }
        raise cherrypy.HTTPRedirect(redirect_url, status=307)


    @access.cookie
    @access.user
    @loadmodel(map={'folder_id': 'folder'}, model='folder', level=AccessType.READ)
    def p0TaskRedirect(self, folder, params):
        return self._taskRedirect('Phase 0', folder, '/uda/gallery#/qc/%(folder_id)s')


    @access.cookie
    @access.user
    @loadmodel(map={'folder_id': 'folder'}, model='folder', level=AccessType.READ)
    def p1aTaskRedirect(self, folder, params):
        return self._taskRedirect('Phase 1a', folder, '/uda/annotate#/%(item_id)s')


    @access.cookie
    @access.user
    @loadmodel(map={'folder_id': 'folder'}, model='folder', level=AccessType.READ)
    def p1bTaskRedirect(self, folder, params):
        return self._taskRedirect('Phase 1b', folder, '/uda/annotate#/%(item_id)s')


    @access.cookie
    @access.user
    @loadmodel(map={'study_id': 'study'}, model='study', plugin='isic_archive', level=AccessType.READ)
    def p2TaskRedirect(self, study, params):
        try:
            active_annotations = self.model('study', 'isic_archive').childAnnotations(
                study=study,
                annotator_user=self.getCurrentUser(),
                state=self.model('study', 'isic_archive').State.ACTIVE,
                limit=1
            )
            next_annotation = active_annotations.sort('name', pymongo.ASCENDING).next()
        except StopIteration:
            raise RestException('Study "%s" has no annotation tasks for this user.' % study['_id'])

        redirect_url = '/uda/map#/%s' % next_annotation['_id']
        raise cherrypy.HTTPRedirect(redirect_url, status=307)
