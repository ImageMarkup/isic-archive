#!/usr/bin/env python
# -*- coding: utf-8 -*-

import collections
import datetime
import itertools
import mimetypes
import operator
import os
import json

import cherrypy
from girder.api import access
from girder.api.rest import Resource, RestException, loadmodel
from girder.api.describe import Description
from girder.constants import AccessType
from girder.models.model_base import AccessException
from girder.utility.model_importer import ModelImporter

from .provision_utility import ISIC, _ISICCollection, getAdminUser


def getItemsInFolder(folder):
    return list(ModelImporter.model('folder').childItems(
        folder,
        filters={'meta.convertedFilename': {'$exists': True}}
    ))


class UDAResource(Resource):
    def __init__(self, plugin_root_dir):
        self.resourceName = 'uda'
        self.plugin_root_dir = plugin_root_dir

        self.route('GET', ('task',), self.taskList)
        self.route('POST', ('task', 'qc', ':folder_id', 'complete'), self.p0TaskComplete)
        self.route('GET', ('task', 'markup', ':item_id'), self.p1or2TaskDetail)
        self.route('POST', ('task', 'markup', ':item_id', 'complete'), self.p1TaskComplete)
        self.route('GET', ('task', 'map', ':item_id'), self.p1or2TaskDetail)


    def _requireCollectionAccess(self, collection_name):
        collection = self.model('collection').findOne({'name': collection_name})
        user = self.getCurrentUser()
        self.model('collection').requireAccess(collection, user, AccessType.READ)
        return collection


    def _getFoldersForCollection(self, collection, excludeFlagged=True):
        def p0FilterFunc(folder):
            if folder['name'] == 'dropzip':
                return False
            if excludeFlagged and folder['name'] == 'flagged':
                return False
            return True

        folders = self.model('folder').find(
            {'parentId': collection['_id']})

        if collection['name'] == 'Phase 0':
            # TODO: do the filtering in the query
            folders = itertools.ifilter(p0FilterFunc, folders)
        return folders


    @access.user
    def taskList(self, params):
        result = list()

        # TODO: make this a global constant somewhere
        PHASE_TASK_URLS = {
            'Phase 0': '/uda/task/p0/%(folder_id)s',
            'Phase 1a': '/uda/task/p1a/%(folder_id)s',
            'Phase 1b': '/uda/task/p1b/%(folder_id)s',
            'Phase 1c': '/uda/task/p1c/%(folder_id)s',
            'Phase 2': '/uda/task/p2/%(folder_id)s'
        }
        for phase_name, task_url in sorted(PHASE_TASK_URLS.iteritems()):
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
                for folder in self._getFoldersForCollection(collection)
            )
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

        contents = json.loads(cherrypy.request.body.read())

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


        # move flagged images into flagged folder, set QC metadata
        # TODO: create "flagged" if not present?
        flagged_folder = ModelImporter.model('folder').findOne({
            'parentId': phase0_collection['_id'],
            'name': 'flagged'
        })
        phase0_flagged_images = _ISICCollection.createFolder(
            name=folder['name'],
            description='',
            parent=flagged_folder,
            parent_type='folder'
        )
        for image_item in flagged_image_items:
            qc_metadata = {
                'qc_user': self.getCurrentUser()['_id'],
                'qc_result': 'flagged',
                'qc_folder_id': folder['_id']
            }
            self.model('item').setMetadata(image_item, qc_metadata)
            self.model('item').move(image_item, phase0_flagged_images)

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
                'qc_folder_id': folder['_id'],
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
    def p1or2TaskDetail(self, item, params):
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
        PREVIOUS_PHASE_CODES = {
            'Phase 1b': 'p1a',
            'Phase 1c': 'p1b',
            'Phase 2': 'p1c'
        }
        previous_phase_code = PREVIOUS_PHASE_CODES.get(phase_name)
        if previous_phase_code:
            return_dict['loadAnnotation'] = True

            previous_phase_annotation_file_name_ending = '-%s.json' % previous_phase_code
            for item_file in sorted(
                    self.model('item').childFiles(item),
                    key=operator.itemgetter('created'),
                    reverse=True
            ):
                if item_file['name'].endswith(previous_phase_annotation_file_name_ending):
                    item_file_generator = self.model('file').download(item_file, headers=False)
                    previous_phase_annotation = json.loads(''.join(item_file_generator()))
                    return_dict['annotation'] = previous_phase_annotation[previous_phase_code]['steps']
                    break
            else:
                # TODO: no file found, raise error
                pass

            if phase_name == 'Phase 2':
                # hardcode a default featureset for now
                featureset = self.model('featureset', 'isic_archive').findOne({'name': 'ISIC Conventional'})

                legacy_featureset = dict()
                for new_level, legacy_level in [
                        ('image_features', 'lesionlevel'),
                        ('region_features', 'tiles')
                        ]:
                    # need to first build an intermediate variable to maintain ordering
                    legacy_questions = collections.OrderedDict()

                    for feature in featureset[new_level]:
                        header = feature['name'][0]
                        legacy_question = {
                            'name': feature['name'][0] if len(feature['name']) == 1 else ': '.join(feature['name'][1:]),
                            'type': feature['type']
                        }
                        if feature['type'] =='select':
                            legacy_question['shortname'] = feature['id']
                            legacy_question['options'] = feature['options']
                        else:
                            legacy_question['id'] = feature['id']
                        legacy_questions.setdefault(header, list()).append(legacy_question)

                    legacy_featureset[legacy_level] = [
                        {'header': header, 'questions': questions}
                        for header, questions in legacy_questions.iteritems()
                    ]

                return_dict['variables'] = legacy_featureset
        else:
            return_dict['loadAnnotation'] = False

        # include static phase config
        phase_config_file_name = '%s.json' % phase_name.replace(' ', '').lower()
        phase_config_file_path = os.path.join(self.plugin_root_dir, 'custom', 'config', phase_config_file_name)
        with open(phase_config_file_path, 'r') as phase_config_file:
            return_dict['decision_tree'] = json.load(phase_config_file)

        return return_dict

    p1or2TaskDetail.description = (
        Description('Get details of a Phase 1 (markup) or Phase 2 (map) task.')
        .responseClass('UDA')
        .param('item_id', 'The item ID.', paramType='path')
        .errorResponse())


    @access.user
    def p1TaskComplete(self, item_id, params):
        markup_str = cherrypy.request.body.read()
        markup_dict = json.loads(markup_str)

        phase_handlers = {
            # phase_full_lower: (phase_acronym, next_phase_collection)
            'Phase 1a': ('p1a', ISIC.Phase1b.collection),
            'Phase 1b': ('p1b', ISIC.Phase1c.collection),
            'Phase 1c': ('p1c', ISIC.LesionImages.collection),
        }
        try:
            phase_acronym, next_phase_collection = phase_handlers[markup_dict['phase']]
        except KeyError:
            # TODO: send the proper error code on failure
            raise
        else:
            self._requireCollectionAccess(markup_dict['phase'])
            result = self._handlePhaseCore(markup_dict, phase_acronym, next_phase_collection)

        return {'status': result}

    p1TaskComplete.description = (
        Description('Complete a Phase 1 (markup) task.')
        .responseClass('UDA')
        .param('item_id', 'The item ID.', paramType='path')
        .errorResponse())


    def _handlePhaseCore(self, markup_dict, phase_acronym, next_phase_collection):
        item_name_base = markup_dict['image']['name'].split('.t')[0]

        item_metadata = {
            '%s_user' % phase_acronym: markup_dict['user']['_id'],
            '%s_result' % phase_acronym: 'ok',
            '%s_folder_id' % phase_acronym: markup_dict['image']['folderId'],
            '%s_start_time' % phase_acronym:
                datetime.datetime.utcfromtimestamp(markup_dict['taskstart'] / 1000.0),
            '%s_stop_time' % phase_acronym:
                datetime.datetime.utcfromtimestamp(markup_dict['taskend'] / 1000.0),
        }

        markup_json = dict()
        markup_json[phase_acronym] = {
            'user': markup_dict['user'],
            'image': markup_dict['image'],
            'result': item_metadata
        }

        markup_json[phase_acronym]['steps'] = markup_dict['steps']

        # grab and remove the b64 png from the dictionary
        png_b64string = markup_dict['steps']['2']['markup']['features'][0]['properties']['parameters'].pop('rgb')
        # remote the initial data uri details
        png_b64string_trim = png_b64string[22:]

        # grab and remove the b64 png from the dictionary
        png_tiles_b64string = markup_dict['steps']['2']['markup']['features'][0]['properties']['parameters'].pop('tiles')
        # remote the initial data uri details
        png_tiles_b64string_trim = png_tiles_b64string[22:]

        # add to existing item
        # TODO: get item_id from URL, instead of within markup_dict
        image_item = self.model('item').load(markup_dict['image']['_id'], force=True)
        self.model('item').setMetadata(image_item, item_metadata)

        def _defaultSerialize(o):
            if isinstance(o, datetime.datetime):
                return o.isoformat()
            raise TypeError(repr(o) + " is not JSON serializable")

        self._createFileFromData(
            image_item,
            json.dumps(markup_json, default=_defaultSerialize),
            '%s-%s.json' % (item_name_base, phase_acronym)
        )

        self._createFileFromData(
            image_item,
            png_b64string_trim.decode('base64'),
            '%s-%s.png' % (item_name_base, phase_acronym)
        )

        self._createFileFromData(
            image_item,
            png_tiles_b64string_trim.decode('base64'),
            '%s-tile-%s.png' % (item_name_base, phase_acronym)
        )

        # move item to folder in next collection
        original_folder = self.model('folder').load(markup_dict['image']['folderId'], force=True)
        next_phase_folder = _ISICCollection.createFolder(
            name=original_folder['name'],
            description=original_folder['description'],
            parent=next_phase_collection,
            parent_type='collection'
        )

        self.model('item').move(image_item, next_phase_folder)

        # remove empty folders in original collection
        if self.model('folder').subtreeCount(original_folder) == 1:
            self.model('folder').remove(original_folder)

        return 'success'


    def _createFileFromData(self, item, data, filename):
        # TODO: overwrite existing files if present, using provenance to keep old files
        upload = self.model('upload').createUpload(
            getAdminUser(),
            filename,
            'item', item,
            len(data),
            mimetypes.guess_type(filename)[0]
        )
        self.model('upload').handleChunk(upload, data)


class TaskHandler(Resource):
    def __init__(self, plugin_root_dir):
        self.resourceName = 'task'
        self.plugin_root_dir = plugin_root_dir

        self.route('GET', (), self.taskDashboard)
        self.route('GET', ('p0', ':folder_id'), self.p0TaskRedirect)
        self.route('GET', ('p1a', ':folder_id'), self.p1aTaskRedirect)
        self.route('GET', ('p1b', ':folder_id'), self.p1bTaskRedirect)
        self.route('GET', ('p1c', ':folder_id'), self.p1cTaskRedirect)
        self.route('GET', ('p2', ':folder_id'), self.p2TaskRedirect)
        # TODO: cookieAuth decorator


    @access.public
    def taskDashboard(self, params):
        return cherrypy.lib.static.serve_file(os.path.join(self.plugin_root_dir, 'custom', 'task.html'))
    taskDashboard.cookieAuth = True


    def _taskRedirect(self, phase_name, folder, url_format):
        collection = self.model('collection').findOne({'name': phase_name})
        if folder['baseParentId'] != collection['_id']:
            raise RestException('Folder "%s" is not in collection "%s"' % (folder['_id'], phase_name))

        items = getItemsInFolder(folder)
        if not items:
            raise RestException('Folder "%s" in collection "%s" is empty' % (folder['_id'], phase_name))

        redirect_url = url_format % {
            'folder_id': folder['_id'],
            'item_id': items[0]['_id']
        }
        raise cherrypy.HTTPRedirect(redirect_url, status=307)


    @access.user
    @loadmodel(map={'folder_id': 'folder'}, model='folder', level=AccessType.READ)
    def p0TaskRedirect(self, folder, params):
        return self._taskRedirect('Phase 0', folder, '/uda/qc/%(folder_id)s')
    p0TaskRedirect.cookieAuth = True


    @access.user
    @loadmodel(map={'folder_id': 'folder'}, model='folder', level=AccessType.READ)
    def p1aTaskRedirect(self, folder, params):
        return self._taskRedirect('Phase 1a', folder, '/uda/annotate/%(item_id)s')
    p1aTaskRedirect.cookieAuth = True


    @access.user
    @loadmodel(map={'folder_id': 'folder'}, model='folder', level=AccessType.READ)
    def p1bTaskRedirect(self, folder, params):
        return self._taskRedirect('Phase 1b', folder, '/uda/annotate/%(item_id)s')
    p1bTaskRedirect.cookieAuth = True


    @access.user
    @loadmodel(map={'folder_id': 'folder'}, model='folder', level=AccessType.READ)
    def p1cTaskRedirect(self, folder, params):
        return self._taskRedirect('Phase 1c', folder, '/uda/annotate/%(item_id)s')
    p1cTaskRedirect.cookieAuth = True


    @access.user
    @loadmodel(map={'folder_id': 'folder'}, model='folder', level=AccessType.READ)
    def p2TaskRedirect(self, folder, params):
        return self._taskRedirect('Phase 2', folder, '/uda/map/%(item_id)s')
    p2TaskRedirect.cookieAuth = True
