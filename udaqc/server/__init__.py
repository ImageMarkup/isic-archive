
from girder.utility.model_importer import ModelImporter
from girder.api.describe import Description
import cherrypy
import os
import datetime



def tasklisthandler(id, params):

    m = ModelImporter()

    user = m.model('user').load(id, force=True)
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



def taskdonehandler(id, params):

    m = ModelImporter()

    # todo: posting as a dictionary, but content is a key?
    # print cherrypy.request.body.read()
    # print params.keys()[0]

    try:

        import json
        contents = json.loads(params.keys()[0])
        print contents.keys()

        good_images = contents['good']
        flagged_images = contents['flagged']
        user_info = contents['user']
        datestr = contents['date']

        print flagged_images



        return {'status' : 'success'}

    except:

        return {
            'status' : 'error in post',
            'received' : params
        }



## returns the qc application

def load(info):

    app_base = os.path.join(os.curdir, os.pardir)
    qc_app_path = os.path.join(app_base, 'qcapp')

    info['config']['/uda/qc'] = {
        'tools.staticfile.on': 'True',
        'tools.staticfile.filename': os.path.abspath(os.path.join(qc_app_path, u'qc.html'))
    }

    # add endpoint to get image list


    info['apiRoot'].user.route('GET', (':id', 'tasklist'), tasklisthandler)
    info['apiRoot'].user.route('POST', (':id', 'tasklist'), taskdonehandler)

