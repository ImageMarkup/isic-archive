# coding=utf-8

import json
import os

import cherrypy
from girder.api import access
from girder.api.describe import Description
from girder.utility.model_importer import ModelImporter


@access.public
def thumbnailhandler(id, params):

    m = ModelImporter()
    item = m.model('item').load(id, force=True)
    files = m.model('item').childFiles(item)

    for firstFile in files:
        if firstFile['exts'][0] == 'tif':
            break
    else:
        raise Exception('Unable to find TIFF file in item %s' % id)

    assetstore = m.model('assetstore').load(firstFile['assetstoreId'])

    # have to fake it for IIP to place nice
    file_path = os.path.join(assetstore['root'], firstFile['path'] + '.tif')
    thumbnail_url = '/fcgi-bin/iipsrv.fcgi?FIF=%s&WID=256&CVT=jpeg' % (file_path)

    raise cherrypy.HTTPRedirect(thumbnail_url)

thumbnailhandler.description = (
    Description('Retrieve the thumbnail for a given item.')
    .param('id', 'The item ID', paramType='path')
    .errorResponse())


@access.public
def annotationHandler(id, params):
    # todo : have it pull the appropriate annotation, it current pulls the last one

    m = ModelImporter()
    item = m.model('item').load(id, force=True)
    files = m.model('item').childFiles(item)

    for firstFile in files:
        if firstFile['exts'][0] == 'json':
            break
    else:
        raise Exception('Unable to find JSON file in item %s' % id)

    json_content_stream = m.model('file').download(firstFile, headers=False)
    annotation_str = json.loads(''.join(json_content_stream()))
    return annotation_str

annotationHandler.description = (
    Description('Retrieve the annotation json for a given item.')
    .param('id', 'The item ID', paramType='path')
    .errorResponse())


@access.public
def segmentationSourceHandler(id, params):
    # todo : have it pull the appropriate annotation, it current pulls the last one

    m = ModelImporter()
    item = m.model('item').load(id, force=True)
    files = m.model('item').childFiles(item)

    for firstFile in files:
        if firstFile['exts'][0] == 'png':
            if 'tile' not in firstFile['name']:
                break
    else:
        raise Exception('Unable to find source PNG file in item %s' % id)

    return m.model('file').download(firstFile, headers=True)

segmentationSourceHandler.description = (
    Description('Retrieve the annotation json for a given item.')
    .param('id', 'The item ID', paramType='path')
    .errorResponse())


@access.public
def segmentationTileHandler(id, params):
    # todo : have it pull the appropriate annotation, it current pulls the last one

    m = ModelImporter()
    item = m.model('item').load(id, force=True)
    files = m.model('item').childFiles(item)

    for firstFile in files:
        if firstFile['exts'][0] == 'png':
            if 'tile' in firstFile['name']:
                break
    else:
        raise Exception('Unable to find tile PNG file in item %s' % id)

    return m.model('file').download(firstFile, headers=True)

segmentationTileHandler.description = (
    Description('Retrieve the annotation json for a given item.')
    .param('id', 'The item ID', paramType='path')
    .errorResponse())


@access.public
def zoomifyhandler(id, params, **kwargs):
    """
    returns the zoomify metadata
    """

    zsplit = cherrypy.url().split('zoomify')

    if len(zsplit) > 1:

        m = ModelImporter()
        item = m.model('item').load(id, force=True)
        files = m.model('item').childFiles(item)

        for firstFile in files:
            if firstFile['exts'][0] == 'tif':
                break
        else:
            raise Exception('Unable to find TIFF file in item %s' % id)

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


@access.public
def fifHandler(id, params, **kwargs):

    zsplit = cherrypy.url().split('fif/')

    if len(zsplit) > 1:

        m = ModelImporter()
        item = m.model('item').load(id, force=True)
        files = m.model('item').childFiles(item)

        for firstFile in files:
            if firstFile['exts'][0] == 'tif':
                break
        else:
            raise Exception('Unable to find TIFF file in item %s' % id)

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
