__author__ = 'stonerri'

from girder.utility.model_importer import ModelImporter
from girder.constants import TerminalColor
from girder.api.describe import Description
import cherrypy
import os
import datetime
import json
from model_utility import *


class TaskHandler(object):
    exposed = True
    def __init__(self):
        pass

    # this line will map the first argument after / to the 'id' parameter
    # for example, a GET request to the url:
    # http://localhost:8000/items/
    # will call GET with id=None
    # and a GET request like this one: http://localhost:8000/items/1
    # will call GET with id=1
    # you can map several arguments using:
    # @cherrypy.propargs('arg1', 'arg2', 'argn')
    # def GET(self, arg1, arg2, argn)

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

        m = ModelImporter()
        user = m.model('user').load(id, force=True)
        task_list = []

        for groupId in user.get('groups', list()):
            group = m.model('group').load(groupId, force=True)
            group_count, group_weight = getWeightForGroup(group['name'])

            task_list.append({
                 'name': group['name'],
                 'count' : group_count,
                 'weight' : group_weight
            })

        final_task = {'weight': 0}

        for task in task_list:
            # print task
            if(task['count'] > 0 and task['weight'] > final_task['weight']):
                final_task = task

        # this is where we'd return something if it was an API, instead we're going one step farther and redirecting to the task



        phase_folders = getFoldersForCollection(getCollection(final_task['name']))

        target_folder = None
        target_count = 0

        for folder in phase_folders:
            items_in_folder = getItemsInFolder(folder)
            if len(items_in_folder) > target_count:
                target_folder = folder
                target_count = len(items_in_folder)


        if target_folder:

            redirect_url = self.urlForPhase(final_task['name'], target_folder['_id'])

            raise cherrypy.HTTPRedirect(redirect_url)

        else:

            return 'no tasks for user'


    # HTML5
    def OPTIONS(self):
        cherrypy.response.headers['Access-Control-Allow-Credentials'] = True
        cherrypy.response.headers['Access-Control-Allow-Origin'] = cherrypy.request.headers['ORIGIN']
        cherrypy.response.headers['Access-Control-Allow-Methods'] = 'GET'
        cherrypy.response.headers['Access-Control-Allow-Headers'] = cherrypy.request.headers['ACCESS-CONTROL-REQUEST-HEADERS']



def tasklisthandler(id, params):

    m = ModelImporter()
    user = m.model('user').load(id, force=True)
    task_list = []

    for groupId in user.get('groups', list()):
        group = m.model('group').load(groupId, force=True)
        group_count, group_weight = getWeightForGroup(group['name'])

        task_list.append({
             'name': group['name'],
             'count' : group_count,
             'weight' : group_weight
        })

    final_task = {'weight': 0}

    for task in task_list:
        # print task
        if(task['count'] > 0 and task['weight'] > final_task['weight']):
            final_task = task


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

    fid = open(config_json, 'r')
    config_list = json.load(fid)
    fid.close()


    return_dict['items'] = [target_items[0]]
    return_dict['folder'] = target_folder
    return_dict['phase'] = final_task['name']


    # non permanent
    if final_task['name'] == 'Phase 1b':

        item = m.model('item').load(target_items[0]['_id'], force=True)
        files = m.model('item').childFiles(item)

        firstFile = None
        for f in files:
            # print f
            if 'p1a.json' in f['name']:
                firstFile = f

        assetstore = m.model('assetstore').load(firstFile['assetstoreId'])
        file_path = os.path.join(assetstore['root'], firstFile['path'])
        json_content = open(file_path, 'r')
        annotation_str = json.load(json_content)
        json_content.close()

        return_dict['loadAnnotation'] = True
        return_dict['annotation'] = annotation_str['p1a']['steps']

    elif final_task['name'] == 'Phase 1c':

        item = m.model('item').load(target_items[0]['_id'], force=True)
        files = m.model('item').childFiles(item)

        firstFile = None
        for f in files:
            # print f
            if 'p1b.json' in f['name']:
                firstFile = f

        assetstore = m.model('assetstore').load(firstFile['assetstoreId'])
        file_path = os.path.join(assetstore['root'], firstFile['path'])
        json_content = open(file_path, 'r')
        annotation_str = json.load(json_content)
        json_content.close()

        return_dict['loadAnnotation'] = True
        return_dict['annotation'] = annotation_str['p1b']['steps']


    elif final_task['name'] == 'Phase 2':

        item = m.model('item').load(target_items[0]['_id'], force=True)
        files = m.model('item').childFiles(item)

        # add annotations
        firstFile = None
        for f in files:
            # print f
            if 'p1c.json' in f['name']:
                firstFile = f

        assetstore = m.model('assetstore').load(firstFile['assetstoreId'])
        file_path = os.path.join(assetstore['root'], firstFile['path'])
        json_content = open(file_path, 'r')
        annotation_str = json.load(json_content)
        json_content.close()

        vars_path = os.path.abspath(os.path.join(app_path, 'phase2-variables.json'))

        fvars = open(vars_path, 'r')
        fvarlist  = json.load(fvars)
        fvars.close()


        return_dict['loadAnnotation'] = True
        return_dict['variables'] = fvarlist
        return_dict['annotation'] = annotation_str['p1c']['steps']

    else:
        return_dict['loadAnnotation'] = False

    # the UI json to provide
    return_dict['decision_tree'] = config_list


    return return_dict


tasklisthandler.description = (
    Description('Retrieve the current task list for a given user')
    .param('id', 'The user ID', paramType='path')
    .errorResponse())


def updateQCStatus(contents):


    m = ModelImporter()

    # TODO we should do some access control on this, but for now going straight through

    # arrive as a list
    good_images = contents['good']

    # arrives as a dict
    flagged_images = contents['flagged']

    # arrives as a dict
    user_info = contents['user']

    # not needed, calculated automatically by model update
    datestr = contents['date']

    # folder info
    folder_info = contents['folder']

    # get folder for flagged images
    phase0_collection =  getCollection('Phase 0')

    phase0_flagged_images = getFolder(phase0_collection, 'flagged')

    # move flagged images into flagged folder, set QC metadata
    for image_key, image in flagged_images.iteritems():

        m_image = m.model('item').load(image['_id'], force=True)

        qc_metadata = {
            'qc_user' : user_info['_id'],
            'qc_result' :  'flagged',
            'qc_folder_id' : folder_info['_id']
        }

        m.model('item').setMetadata(m_image, qc_metadata)
        m_image['folderId'] = phase0_flagged_images['_id']
        m.model('item').updateItem(m_image)


    uda_user = getUDAuser()
    phase1a_collection = getCollection('Phase 1a')
    phase1a_images = makeFolderIfNotPresent(phase1a_collection, folder_info['name'], '', 'collection', False, uda_user)

    # move good images into phase 1a folder
    for image in good_images:

        m_image = m.model('item').load(image['_id'], force=True)

        qc_metadata = {
            'qc_user' : user_info['_id'],
            'qc_result' :  'ok',
            'qc_folder_id' : folder_info['_id']
        }

        m.model('item').setMetadata(m_image, qc_metadata)

        m_image['folderId'] = phase1a_images['_id']
        m.model('item').updateItem(m_image)




def taskCompleteHandler(id, tasktype, params):

    # todo: posting as a dictionary, but content is a key?
    # print cherrypy.request.body.read()

    # branch on task type

    result = 'invalid post'

    if tasktype == 'qc':

        qc_contents = json.loads(params.keys()[0])
        if qc_contents:
            updateQCStatus(qc_contents)
            result = 'success'

    if tasktype in ['markup', 'map']:

        markup_str = cherrypy.request.body.read()
        markup_dict = json.loads(markup_str)

        phase_handlers = {
            'phase 1a': handlePhase1a,
            'phase 1b': handlePhase1b,
            'phase 1c': handlePhase1c,
            'phase 2': handlePhase2
        }
        try:
            phase_handler = phase_handlers[markup_dict['phase'].lower()]
        except KeyError:
            # TODO: fail here
            print markup_dict
            result = 'not implemented yet'
        else:
            result = phase_handler(markup_dict)

    return {'status': result}


def handlePhase1a(markup_dict):
    return handlePhaseCore(markup_dict, 'p1a', 'Phase 1b')


def handlePhase1b(markup_dict):
    return handlePhaseCore(markup_dict, 'p1b', 'Phase 1c')


def handlePhase1c(markup_dict):
    return handlePhaseCore(markup_dict, 'p1c', 'Phase 2')


def handlePhase2(markup_dict):
    # TODO: auto-create "Complete" collection owned by "udastudy"
    return handlePhaseCore(markup_dict, 'p2', 'Complete')


def handlePhaseCore(markup_dict, phase_acronym, next_phase_full):
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
        markup_json[phase_acronym]['steps'] = markup_dict['steps'],

        # grab the b64 png from the dictionary
        png_b64string = \
        markup_dict['steps']['2']['markup']['features'][0]['properties'][
            'parameters']['rgb']
        # remote the initial data uri details
        png_b64string_trim = png_b64string[22:]

        # make sure it's not in the final project
        del markup_json[phase_acronym]['steps']['2']['markup']['features'][0][
            'properties']['parameters']['rgb']

        # grab the b64 png from the dictionary
        png_tiles_b64string = \
        markup_dict['steps']['2']['markup']['features'][0]['properties'][
            'parameters']['tiles']
        # remote the initial data uri details
        png_tiles_b64string_trim = png_tiles_b64string[22:]

        # make sure it's not in the final project
        del markup_json[phase_acronym]['steps']['2']['markup']['features'][0][
            'properties']['parameters']['tiles']

    elif phase_acronym == 'p2':
        markup_json[phase_acronym]['user_annotation'] = markup_dict[
            'user_annotation']
        markup_json[phase_acronym]['markup_model'] = markup_dict['markup_model']
        # TODO: dereference annotation_options


    # add to existing item
    m = ModelImporter()
    image_item = m.model('item').load(markup_dict['image']['_id'], force=True)
    m.model('item').setMetadata(image_item, item_metadata)


    # move item to folder in next collection
    original_folder = m.model('folder').load(markup_dict['image']['folderId'], force=True)
    next_phase_folder = makeFolderIfNotPresent(
        getCollection(next_phase_full),
        original_folder['name'], '',
        'collection', False, getUDAuser())
    image_item['folderId'] = next_phase_folder['_id']
    m.model('item').updateItem(image_item)


    # add new files to the item
    assetstore = getAssetStoreForItem(image_item)

    markup_json_file_name = '%s-%s.json' % (item_name_base, phase_acronym)
    markup_json_data = json.dumps(markup_json)
    json_file = createFileObjectFromData(markup_json_file_name, image_item, assetstore, markup_json_data, 'w')

    if phase_acronym in ['p1a', 'p1b', 'p1c']:
        png_annotation_file_name = '%s-%s.png' % (item_name_base, phase_acronym)
        png_annotation_data = png_b64string_trim.decode('base64')
        png_file = createFileObjectFromData(png_annotation_file_name, image_item, assetstore, png_annotation_data, 'wb')

        png_tile_annotation_file_name = '%s-tile-%s.png' % (item_name_base, phase_acronym)
        png_tile_annotation_data = png_tiles_b64string_trim.decode('base64')
        png_tile_file = createFileObjectFromData(png_tile_annotation_file_name,
                                                 image_item, assetstore,
                                                 png_tile_annotation_data, 'wb')


    return 'success'


taskCompleteHandler.description = (
    Description('Push the QC results for the current task list for a given user')
    .param('id', 'The user ID', paramType='path')
    .errorResponse())
