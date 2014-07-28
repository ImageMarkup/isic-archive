__author__ = 'stonerri'

from girder.utility.model_importer import ModelImporter
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

        return url


    @cherrypy.popargs('id')
    def GET(self, id=None):

        m = ModelImporter()
        user = m.model('user').load(id, force=True)
        task_list = []

        for groupId in user['groups']:
            group = m.model('group').load(groupId, force=True)
            group_count, group_weight = getWeightForGroup(group['name'])

            task_list.append({
                 'name': group['name'],
                 'count' : group_count,
                 'weight' : group_weight
            })

        final_task = {'weight': 0}

        for task in task_list:
            print task
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

    for groupId in user['groups']:
        group = m.model('group').load(groupId, force=True)
        group_count, group_weight = getWeightForGroup(group['name'])

        task_list.append({
             'name': group['name'],
             'count' : group_count,
             'weight' : group_weight
        })

    final_task = {'weight': 0}

    for task in task_list:
        print task
        if(task['count'] > 0 and task['weight'] > final_task['weight']):
            final_task = task


    phase_folders = getFoldersForCollection(getCollection(final_task['name']))

    target_folder = None
    target_count = 0
    target_items = []

    for folder in phase_folders:
        items_in_folder = getItemsInFolder(folder)
        if len(items_in_folder) > target_count:
            target_folder = folder
            target_count = len(items_in_folder)
            target_items = items_in_folder


    return_dict = {}


    # todo: branch for configs

    app_base = os.path.join(os.curdir, os.pardir)
    qc_app_path = os.path.join(app_base, 'udaapp', 'config')
    config_json = os.path.abspath(os.path.join(qc_app_path, u'phase1a.json'))

    fid = open(config_json, 'r')
    config_list = json.load(fid)
    fid.close()


    return_dict['items'] = target_items
    return_dict['folder'] = target_folder
    return_dict['phase'] = final_task['name']

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

    status = {'status' : 'failed'}

    if tasktype == 'qc':

        qc_contents = json.loads(params.keys()[0])
        if qc_contents:
            updateQCStatus(qc_contents)
            status = {'status' : 'success'}

    if tasktype == 'markup':

        markup_str = cherrypy.request.body.read()
        markup_dict = json.loads(markup_str)

        # print type(markup_dict)
        # print markup_dict.keys()

        from pprint import pprint as pp
        pp(markup_dict)

        # print params



    return status





taskCompleteHandler.description = (
    Description('Push the QC results for the current task list for a given user')
    .param('id', 'The user ID', paramType='path')
    .errorResponse())

