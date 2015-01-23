# coding=utf-8

import datetime
import itertools
import mimetypes
import operator
import os
import json

import cherrypy
from girder.api import access
from girder.api.rest import Resource
from girder.api.describe import Description
from girder.constants import AccessType
from girder.models.model_base import AccessException
from girder.utility.model_importer import ModelImporter

from .model_utility import *
from .provision_utility import getOrCreateUDAFolder


class UDAResource(Resource):
    def __init__(self):
        self.resourceName = 'uda'
        self.route('GET', ('task',), self.taskList)
        self.route('POST', ('task', 'qc', 'complete'), self.p0TaskComplete)
        self.route('POST', ('task', 'markup', ':item_id', 'complete'), self.p1TaskComplete)
        self.route('POST', ('task', 'map', ':item_id', 'complete'), self.p2TaskComplete)


    def _requireCollectionAccess(self, collection_name):
        collection = self.model('collection').findOne({'name': collection_name})
        user = self.getCurrentUser()
        self.model('collection').requireAccess(collection, user, AccessType.READ)



    @access.user
    def taskList(self, params):
        result = list()

        # TODO: make this a global constant somewhere
        phase_names = ['Phase 0', 'Phase 1a', 'Phase 1b', 'Phase 1c', 'Phase 2']
        for phase_name in phase_names:
            try:
                self._requireCollectionAccess(phase_name)
            except AccessException:
                continue

            result.append({
                'phase': phase_name,
                'count': countImagesInCollection(phase_name),
                'url': '/uda/annotate', # TODO
            })

        return result

    taskList.description = (
        Description('List available tasks.')
        .responseClass('UDA')
        .errorResponse())





    @access.user
    def p0TaskComplete(self, params):
        self._requireCollectionAccess('Phase 0')
        contents = json.loads(cherrypy.request.body.read())

        good_images_list = contents['good']
        flagged_images_dict = contents['flagged']
        # TODO: lookup folder from ID
        folder_info = contents['folder']
        current_user = self.getCurrentUser()

        # move flagged images into flagged folder, set QC metadata
        phase0_collection = self.model('collection').findOne({'name': 'Phase 0'})
        phase0_flagged_images = getFolder(phase0_collection, 'flagged')
        # TODO: create "flagged" if not present?
        for image in flagged_images_dict.itervalues():
            image_item = self.model('item').load(image['_id'], force=True)
            # TODO: ensure this image item is actually in Phase 0
            qc_metadata = {
                'qc_user': current_user['_id'],
                'qc_result': 'flagged',
                'qc_folder_id': folder_info['_id']
            }
            self.model('item').setMetadata(image_item, qc_metadata)
            self.model('item').move(image_item, phase0_flagged_images)

        # move good images into phase 1a folder
        phase1a_collection = self.model('collection').findOne({'name': 'Phase 1a'})
        phase1a_images = getOrCreateUDAFolder(
            name=folder_info['name'],
            description=folder_info['description'],
            parent=phase1a_collection,
            parent_type='collection'
        )
        for image in good_images_list:
            image_item = self.model('item').load(image['_id'], force=True)
            # TODO: ensure this image item is actually in Phase 0
            qc_metadata = {
                'qc_user': current_user['_id'],
                'qc_result': 'ok',
                'qc_folder_id': folder_info['_id'],
                'qc_stop_time': datetime.datetime.utcnow(),
            }
            self.model('item').setMetadata(image_item, qc_metadata)
            self.model('item').move(image_item, phase1a_images)

        return {'status': 'success'}

    p0TaskComplete.description = (
        Description('Complete a Phase 0 (qc) task.')
        .responseClass('UDA')
        .param('details', 'JSON details of images to be QC\'d.', paramType='body')
        .errorResponse())


    @access.user
    def p1TaskComplete(self, item_id, params):
        markup_str = cherrypy.request.body.read()
        markup_dict = json.loads(markup_str)

        phase_handlers = {
            # phase_full_lower: (phase_acronym, next_phase_full)
            'Phase 1a': ('p1a', 'Phase 1b'),
            'Phase 1b': ('p1b', 'Phase 1c'),
            'Phase 1c': ('p1c', 'Phase 2'),
        }
        try:
            phase_acronym, next_phase_full = phase_handlers[markup_dict['phase']]
        except KeyError:
            # TODO: send the proper error code on failure
            raise
        else:
            self._requireCollectionAccess(markup_dict['phase'])
            result = self._handlePhaseCore(markup_dict, phase_acronym, next_phase_full)

        return {'status': result}

    p1TaskComplete.description = (
        Description('Complete a Phase 1 (markup) task.')
        .responseClass('UDA')
        .param('item_id', 'The item ID.', paramType='path')
        .errorResponse())


    @access.user
    def p2TaskComplete(self, item_id, params):
        self._requireCollectionAccess('Phase 2')
        markup_str = cherrypy.request.body.read()
        markup_dict = json.loads(markup_str)

        # TODO: auto-create "Complete" collection owned by "udastudy"
        result = self._handlePhaseCore(markup_dict, 'p2', 'Complete')

        return {'status': result}

    p2TaskComplete.description = (
        Description('Complete a Phase 2 (map) task.')
        .responseClass('UDA')
        .param('item_id', 'The item ID.', paramType='path')
        .errorResponse())


    def _handlePhaseCore(self, markup_dict, phase_acronym, next_phase_full):
        item_name_base = markup_dict['image']['name'].split('.t')[0]

        item_metadata = {
            '%s_user' % phase_acronym: markup_dict['user']['_id'],
            '%s_result' % phase_acronym: 'ok',
            '%s_folder_id' % phase_acronym: markup_dict['image']['folderId'],
            '%s_start_time' % phase_acronym: markup_dict['taskstart'],
            '%s_stop_time' % phase_acronym: markup_dict['taskend'],
        }

        markup_json = dict()
        markup_json[phase_acronym] = {
            'user': markup_dict['user'],
            'image': markup_dict['image'],
            'result': item_metadata
        }

        if phase_acronym in ['p1a', 'p1b', 'p1c']:
            markup_json[phase_acronym]['steps'] = markup_dict['steps']

            # grab and remove the b64 png from the dictionary
            png_b64string = markup_dict['steps']['2']['markup']['features'][0]['properties']['parameters'].pop('rgb')
            # remote the initial data uri details
            png_b64string_trim = png_b64string[22:]

            # grab and remove the b64 png from the dictionary
            png_tiles_b64string = markup_dict['steps']['2']['markup']['features'][0]['properties']['parameters'].pop('tiles')
            # remote the initial data uri details
            png_tiles_b64string_trim = png_tiles_b64string[22:]

        elif phase_acronym == 'p2':
            markup_json[phase_acronym]['user_annotation'] = markup_dict['user_annotation']
            markup_json[phase_acronym]['markup_model'] = markup_dict['markup_model']
            # TODO: dereference annotation_options

        # add to existing item
        # TODO: get item_id from URL, instead of within markup_dict
        image_item = self.model('item').load(markup_dict['image']['_id'], force=True)
        self.model('item').setMetadata(image_item, item_metadata)

        # move item to folder in next collection
        original_folder = self.model('folder').load(markup_dict['image']['folderId'], force=True)

        next_phase_folder = getOrCreateUDAFolder(
            name=original_folder['name'],
            description=original_folder['description'],
            parent=getCollection(next_phase_full),
            parent_type='collection'
        )

        image_item['folderId'] = next_phase_folder['_id']
        self.model('item').updateItem(image_item)

        self._createFileFromData(
            image_item,
            json.dumps(markup_json),
            '%s-%s.json' % (item_name_base, phase_acronym)
        )

        if phase_acronym in ['p1a', 'p1b', 'p1c']:
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

        return 'success'


    def _createFileFromData(self, item, data, filename):
        # TODO: overwrite existing files if present, using provenance to keep old files
        upload = self.model('upload').createUpload(
            getUDAuser(),
            filename,
            'item', item,
            len(data),
            mimetypes.guess_type(filename)[0]
        )
        self.model('upload').handleChunk(upload, data)










def getFinalTask(user_id):
    # assign a weight to phase
    phase_weights = {
        'Phase 0': 10,
        'Phase 1a': 20,
        'Phase 1b': 30,
        'Phase 1c': 40,
        'Phase 2': 60,
    }

    user = ModelImporter.model('user').load(user_id, force=True)
    task_list = []

    for groupId in user.get('groups', list()):
        group_name = ModelImporter.model('group').load(groupId, force=True)['name']

        task_list.append({
            'name': group_name,
            'count': countImagesInCollection(group_name),
            'weight': phase_weights.get(group_name, 0)
        })

    final_task = {'weight': 0}

    for task in task_list:
        # print task
        if task['count'] > 0 and task['weight'] > final_task['weight']:
            final_task = task

    return final_task



class TaskHandler(object):
    exposed = True

    def urlForPhase(self, phaseName, param=None):

        url = '/'

        # assign a weight to phase
        if phaseName == 'Phase 0':
            url = '/uda/qc/%s' % param
        elif phaseName == 'Phase 1a':
            url = '/uda/annotate'
        elif phaseName == 'Phase 1b':
            url = '/uda/annotate'
        elif phaseName == 'Phase 1c':
            url = '/uda/annotate'
        elif phaseName == 'Phase 2':
            url = '/uda/map'

        return url


    @cherrypy.popargs('id')
    def GET(self, id=None):
        final_task = getFinalTask(id)

        # this is where we'd return something if it was an API, instead we're going one step farther and redirecting to the task

        # todo: if user isn't a member of any groups with tasks, "final_task['name']" raises a KeyError

        phase_folders = getFoldersForCollection(getCollection(final_task['name']))

        target_folder = None
        target_count = 0

        for folder in phase_folders:
            items_in_folder = getItemsInFolder(folder)
            if len(items_in_folder) > target_count:
                target_folder = folder
                target_count = len(items_in_folder)

        # TODO: this breaks if there are more items in "dropzip" than were actually extracted

        if target_folder:
            redirect_url = self.urlForPhase(final_task['name'], target_folder['_id'])
            raise cherrypy.HTTPRedirect(redirect_url)
        else:
            return 'no tasks for user'


@access.public
def tasklisthandler(id, params):
    final_task = getFinalTask(id)

    phase_folders = getFoldersForCollection(getCollection(final_task['name']))

    target_folder = None
    target_count = 0
    target_items = []

    for folder in phase_folders:
        items_in_folder = getItemsInFolder(folder)
        # print '###', folder
        if len(items_in_folder) > target_count:
            target_folder = folder
            target_count = len(items_in_folder)
            target_items = items_in_folder


    return_dict = {}

    # todo: branch for configs


    # TODO: can Girder provide the location of this plugin's directory?
    #  could we reliably use this Python file's location?
    app_base = os.getcwd()  # e.g. /home/ubuntu/applications/girder

    app_path = os.path.join(app_base, 'plugins', 'uda', 'custom', 'config')

    # get the appropriate jsno
    phasejson = final_task['name'].replace(" ", "").lower() + '.json'

    config_json = os.path.abspath(os.path.join(app_path, phasejson))

    with open(config_json, 'r') as fid:
        config_list = json.load(fid)

    return_dict['items'] = [target_items[0]]
    return_dict['folder'] = target_folder
    return_dict['phase'] = final_task['name']

    m = ModelImporter
    if final_task['name'] in ['Phase 1b', 'Phase 1c', 'Phase 2']:
        item = m.model('item').load(target_items[0]['_id'], force=True)
        files = m.model('item').childFiles(item)

        previous_phase_codes = {
            'Phase 1b': 'p1a',
            'Phase 1c': 'p1b',
            'Phase 2': 'p1c'
        }
        previous_phase_code = previous_phase_codes[final_task['name']]
        target_file_name = '%s.json' % previous_phase_code

        firstFile = sorted(
            itertools.ifilter(lambda f: target_file_name in f['name'], files),
            key=operator.itemgetter('created')
        )[-1]
        # TODO: handle when no files are found

        assetstore = m.model('assetstore').load(firstFile['assetstoreId'])
        file_path = os.path.join(assetstore['root'], firstFile['path'])
        with open(file_path, 'r') as json_content:
            annotation_str = json.load(json_content)

        return_dict['loadAnnotation'] = True
        return_dict['annotation'] = annotation_str[previous_phase_code]['steps']

        if final_task['name'] == 'Phase 2':
            vars_path = os.path.abspath(os.path.join(app_path, 'phase2-variables.json'))
            with open(vars_path, 'r') as fvars:
                fvarlist = json.load(fvars)
            return_dict['variables'] = fvarlist

    else:
        return_dict['loadAnnotation'] = False

    # the UI json to provide
    return_dict['decision_tree'] = config_list

    return return_dict

tasklisthandler.description = (
    Description('Retrieve the current task list for a given user')
    .param('id', 'The user ID', paramType='path')
    .errorResponse())
