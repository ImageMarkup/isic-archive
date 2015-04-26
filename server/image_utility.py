#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

import cherrypy
from girder.api import access
from girder.api.describe import Description
from girder.api.rest import loadmodel, RestException
from girder.constants import AccessType
from girder.utility.model_importer import ModelImporter


@access.public
@loadmodel(map={'item_id': 'item'}, model='item', level=AccessType.READ)
def thumbnailhandler(item, params):
    image_file = ModelImporter.model('file').fineOne({
        'itemId': item['_id'],
        'name': item['meta']['convertedFilename']
    })
    if not image_file:
        raise RestException('No TIFF file in item')

    assetstore = ModelImporter.model('assetstore').load(image_file['assetstoreId'])

    # have to fake it for IIP to play nice
    file_path = os.path.join(assetstore['root'], image_file['path'])
    thumbnail_url = '/fcgi-bin/iipsrv.fcgi?FIF=%s&WID=256&CVT=jpeg' % file_path

    raise cherrypy.HTTPRedirect(thumbnail_url, status=307)

thumbnailhandler.cookieAuth = True
thumbnailhandler.description = (
    Description('Retrieve the thumbnail for a given item.')
    .param('item_id', 'The item ID', paramType='path')
    .errorResponse())


@access.public
@loadmodel(map={'item_id': 'item'}, model='item', level=AccessType.READ)
def segmentationSourceHandler(item, params):
    # todo : have it pull the appropriate annotation, it current pulls the last one

    files = ModelImporter.model('item').childFiles(item)

    for firstFile in files:
        if firstFile['exts'][0] == 'png':
            if 'tile' not in firstFile['name']:
                break
    else:
        raise RestException('No source PNG file in item')

    return ModelImporter.model('file').download(firstFile, headers=True)

segmentationSourceHandler.cookieAuth = True
segmentationSourceHandler.description = (
    Description('Retrieve the annotation json for a given item.')
    .param('item_id', 'The item ID', paramType='path')
    .errorResponse())


@access.public
@loadmodel(map={'item_id': 'item'}, model='item', level=AccessType.READ)
def segmentationTileHandler(item, params):
    # todo : have it pull the appropriate annotation, it current pulls the last one

    files = ModelImporter.model('item').childFiles(item)

    for firstFile in files:
        if firstFile['exts'][0] == 'png':
            if 'tile' in firstFile['name']:
                break
    else:
        raise RestException('No tile PNG file in item')

    return ModelImporter.model('file').download(firstFile, headers=True)

segmentationTileHandler.cookieAuth = True
segmentationTileHandler.description = (
    Description('Retrieve the annotation json for a given item.')
    .param('item_id', 'The item ID', paramType='path')
    .errorResponse())


@access.public
@loadmodel(map={'item_id': 'item'}, model='item', level=AccessType.READ)
def zoomifyhandler(item, params, **kwargs):
    """
    returns the zoomify metadata
    """

    zsplit = cherrypy.url().split('zoomify')

    if len(zsplit) > 1:
        image_file = ModelImporter.model('file').findOne({
            'itemId': item['_id'],
            'name': item['meta']['convertedFilename']
        })
        if not image_file:
            raise RestException('No TIFF file in item')

        assetstore = ModelImporter.model('assetstore').load(image_file['assetstoreId'])

        # have to fake it for IIP to place nice
        file_path = os.path.join(assetstore['root'], image_file['path'])
        zoomify_url = '/fcgi-bin/iipsrv.fcgi?Zoomify=%s%s' % (file_path, zsplit[1])

        raise cherrypy.HTTPRedirect(zoomify_url, status=307)

    return 'invalid url'

zoomifyhandler.cookieAuth = True
zoomifyhandler.description = (
    Description('Retrieves the zoomify root path for a given item.')
    .param('item_id', 'The item ID', paramType='path')
    .errorResponse())


@access.public
@loadmodel(map={'item_id': 'item'}, model='item', level=AccessType.READ)
def fifHandler(item, params, **kwargs):

    zsplit = cherrypy.url().split('fif/')

    if len(zsplit) > 1:
        image_file = ModelImporter.model('file').findOne({
            'itemId': item['_id'],
            'name': item['meta']['convertedFilename']
        })
        if not image_file:
            raise RestException('No TIFF file in item')

        assetstore = ModelImporter.model('assetstore').load(image_file['assetstoreId'])

        # have to fake it for IIP to place nice
        file_path = os.path.join(assetstore['root'], image_file['path'])
        zoomify_url = '/fcgi-bin/iipsrv.fcgi?FIF=%s%s' % (file_path, zsplit[1])

        raise cherrypy.HTTPRedirect(zoomify_url, status=307)

    return 'invalid url'

fifHandler.cookieAuth = True
fifHandler.description = (
    Description('Retrieves the FIF IIP root path for a given item.')
    .param('item_id', 'The item ID', paramType='path')
    .errorResponse())
