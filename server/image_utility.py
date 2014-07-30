__author__ = 'stonerri'



from girder.utility.model_importer import ModelImporter
from girder.api.describe import Description
from girder.constants import TerminalColor
import cherrypy
import json
import os
from cherrypy.lib import file_generator

def thumbnailhandler(id, params):

    m = ModelImporter()
    item = m.model('item').load(id, force=True)
    files = m.model('item').childFiles(item)

    firstFile = None
    for f in files:
        # print f
        if f['exts'][0] == 'tif':
            firstFile = f

    print firstFile

    assetstore = m.model('assetstore').load(firstFile['assetstoreId'])

    # have to fake it for IIP to place nice
    file_path = os.path.join(assetstore['root'], firstFile['path'] + '.tif')
    thumbnail_url = '/fcgi-bin/iipsrv.fcgi?FIF=%s&WID=256&CVT=jpeg' % (file_path)

    raise cherrypy.HTTPRedirect(thumbnail_url)


thumbnailhandler.description = (
    Description('Retrieve the thumbnail for a given item.')
    .param('id', 'The item ID', paramType='path')
    .errorResponse())


def annotationHandler(id, params):

    m = ModelImporter()
    item = m.model('item').load(id, force=True)
    files = m.model('item').childFiles(item)

    firstFile = None
    for f in files:
        # print f
        if f['exts'][0] == 'json':
            firstFile = f

    assetstore = m.model('assetstore').load(firstFile['assetstoreId'])
    file_path = os.path.join(assetstore['root'], firstFile['path'])
    json_content = open(file_path, 'r')
    annotation_str = json.load(json_content)
    json_content.close()

    return annotation_str

annotationHandler.description = (
    Description('Retrieve the annotation json for a given item.')
    .param('id', 'The item ID', paramType='path')
    .errorResponse())




def segmentationHandler(id, params):

    m = ModelImporter()
    item = m.model('item').load(id, force=True)
    files = m.model('item').childFiles(item)

    firstFile = None
    for f in files:
        # print f
        if f['exts'][0] == 'png':
            firstFile = f

    assetstore = m.model('assetstore').load(firstFile['assetstoreId'])
    file_path = os.path.join(assetstore['root'], firstFile['path'])

    from cherrypy.lib import file_generator
    cherrypy.response.headers['Content-Type'] = "image/png"
    png_handle = open(file_path, 'rb')
    return file_generator(png_handle)

    #
    # def streamPng():
    #     with open(file_path, 'rb') as f:
    #         yield f.read()
    # return streamPng



segmentationHandler.description = (
    Description('Retrieve the annotation json for a given item.')
    .param('id', 'The item ID', paramType='path')
    .errorResponse())







## returns the zoomify metadata
def zoomifyhandler(id, params, **kwargs):


    zsplit = cherrypy.url().split('zoomify')

    # print params
    # print kwargs

    if len(zsplit) > 1:

        m = ModelImporter()
        item = m.model('item').load(id, force=True)
        files = m.model('item').childFiles(item)

        firstFile = None
        for f in files:
            # print f
            if f['exts'][0] == 'tif':
                firstFile = f
        print firstFile

        assetstore = m.model('assetstore').load(firstFile['assetstoreId'])

        # have to fake it for IIP to place nice
        file_path = os.path.join(assetstore['root'], firstFile['path'] + '.tif')
        zoomify_url = '/fcgi-bin/iipsrv.fcgi?Zoomify=%s%s' % (file_path, zsplit[1])

        raise cherrypy.HTTPRedirect(zoomify_url)

    return 'invalid url'



zoomifyhandler.description = (
    Description('Retrieves the zoomify root path for a given item.')
    .param('id', 'The item ID', paramType='path')
    .errorResponse())




def fifHandler(id, params, **kwargs):

    zsplit = cherrypy.url().split('fif/')

    if len(zsplit) > 1:

        m = ModelImporter()
        item = m.model('item').load(id, force=True)
        files = m.model('item').childFiles(item)

        firstFile = None
        for f in files:
            # print f
            if f['exts'][0] == 'tif':
                firstFile = f
        print firstFile


        assetstore = m.model('assetstore').load(firstFile['assetstoreId'])

        # have to fake it for IIP to place nice
        file_path = os.path.join(assetstore['root'], firstFile['path'] + '.tif')
        zoomify_url = '/fcgi-bin/iipsrv.fcgi?FIF=%s%s' % (file_path, zsplit[1])

        raise cherrypy.HTTPRedirect(zoomify_url)

    return 'invalid url'



fifHandler.description = (
    Description('Retrieves the FIF IIP root path for a given item.')
    .param('id', 'The item ID', paramType='path')
    .errorResponse())

