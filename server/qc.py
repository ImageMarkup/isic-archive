__author__ = 'stonerri'

from girder.utility.model_importer import ModelImporter
from girder.api.describe import Description
import cherrypy
import os
import datetime

from model_utility import *

def tasklisthandler(id, params):

    m = ModelImporter()

    user = m.model('user').load(id, force=True)

    #todo branch based on user information

    phase0_collection =  m.model('collection').find({'name':'Phase 0'})[0]
    phase0_folder_query = m.model('folder').find(
    { '$and' : [
        {'parentId': phase0_collection['_id']},
        {'name': 'images'}
    ]})

    phase0_images = phase0_folder_query[0]

    # switch depending on user,

    images = m.model('item').find({'folderId': phase0_images['_id']})

    tasklist = {}
    imagelist = []

    for image in images:

        imagelist.append(image)

    tasklist['description'] = 'Task list for Phase 0'
    tasklist['images'] = imagelist
    tasklist['date'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


    return tasklist

    # raise cherrypy.HTTPRedirect(thumbnail_url)


tasklisthandler.description = (
    Description('Retrieve the current task list for a given user')
    .param('id', 'The user ID', paramType='path')
    .errorResponse())



def taskCompleteHandler(id, params):

    m = ModelImporter()

    # todo: posting as a dictionary, but content is a key?
    # print cherrypy.request.body.read()



    try:

        # TODO we should do some access control on this, but for now going straight through

        import json

        contents = json.loads(params.keys()[0])

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


        return {'status' : 'success'}

    except:

        return {
            'status' : 'error in post',
            'received' : params
        }


taskCompleteHandler.description = (
    Description('Push the QC results for the current task list for a given user')
    .param('id', 'The user ID', paramType='path')
    .errorResponse())




class QCHandler(object):
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

    @cherrypy.popargs('id')
    def GET(self, id=None):

        app_base = os.path.join(os.curdir, os.pardir)
        qc_app_path = os.path.join(app_base, 'udaapp')
        gallery_html = os.path.abspath(os.path.join(qc_app_path, u'qc.html'))

        fid = open(gallery_html, 'r')
        gallery_content = fid.read()
        fid.close()

        return gallery_content


    # HTML5
    def OPTIONS(self):
        cherrypy.response.headers['Access-Control-Allow-Credentials'] = True
        cherrypy.response.headers['Access-Control-Allow-Origin'] = cherrypy.request.headers['ORIGIN']
        cherrypy.response.headers['Access-Control-Allow-Methods'] = 'GET'
        cherrypy.response.headers['Access-Control-Allow-Headers'] = cherrypy.request.headers['ACCESS-CONTROL-REQUEST-HEADERS']


