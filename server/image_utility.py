#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re

import cherrypy
import pymongo

from girder.api import access
from girder.api.describe import Description
from girder.api.rest import loadmodel, RestException, setRawResponse
from girder.constants import AccessType, SortDir
from girder.utility.model_importer import ModelImporter

from .models.segmentation_helpers.scikit import ScikitSegmentationHelper


# TODO: this function should be safe to remove, but test everything first
@access.public
@loadmodel(map={'item_id': 'item'}, model='item', level=AccessType.READ)
def thumbnailhandler(item, params):
    thumbnail_url = ModelImporter.model('image', 'isic_archive').tileServerURL(item, width=256)
    raise cherrypy.HTTPRedirect(thumbnail_url, status=307)

thumbnailhandler.cookieAuth = True
thumbnailhandler.description = (
    Description('Retrieve the thumbnail for a given image item.')
    .param('item_id', 'The item ID', paramType='path')
    .errorResponse())


@access.public
@loadmodel(map={'item_id': 'item'}, model='item', level=AccessType.READ)
def segmentationSourceHandler(item, params):
    # if item['meta']['studyId'] == ObjectId('567864779fc3c148a0c9b248'):
    if True:
        return ModelImporter.model('file').download(
            ModelImporter.model('image', 'isic_archive').originalFile(item),
            headers=True)

    files = ModelImporter.model('item').childFiles(item, sort=[('created', pymongo.DESCENDING)])

    for first_file in files:
        if first_file['mimeType'] == 'image/png':
            # this is a hack; we should use negative lookahead assertions instead
            if re.search(r'-p1.\.png$', first_file['name']) and not re.search(r'-tile-p1.\.png$', first_file['name']):
                break
    else:
        raise RestException('No source PNG file in item')

    file_download = ModelImporter.model('file').download(first_file, headers=True)
    cherrypy.response.headers['Content-Disposition'] = 'inline; filename="%s"' % first_file['name']
    return file_download

segmentationSourceHandler.cookieAuth = True
segmentationSourceHandler.description = (
    Description('Retrieve segmentation source PNG image for a given image item.')
    .param('item_id', 'The item ID', paramType='path')
    .errorResponse())


@access.public
@loadmodel(map={'item_id': 'item'}, model='item', level=AccessType.READ)
def segmentationTileHandler(item, params):
    # if item['meta']['studyId'] == ObjectId('567864779fc3c148a0c9b248'):
    if True:
        Segmentation = ModelImporter.model('segmentation', 'isic_archive')
        segmentation = Segmentation.findOne(
            {'imageId': item['_id']},
            sort=[('created', SortDir.DESCENDING)]
        )
        superpixels_file = Segmentation.superpixelsFile(segmentation)
        return ModelImporter.model('file').download(
            superpixels_file, headers=True)

    files = ModelImporter.model('item').childFiles(item, sort=[('created', pymongo.DESCENDING)])

    for first_file in files:
        if first_file['mimeType'] == 'image/png':
            if re.search(r'-tile-p1.\.png$', first_file['name']):
                break
    else:
        raise RestException('No tile PNG file in item')

    file_download = ModelImporter.model('file').download(first_file, headers=True)
    cherrypy.response.headers['Content-Disposition'] = 'inline; filename="%s"' % first_file['name']
    return file_download

segmentationTileHandler.cookieAuth = True
segmentationTileHandler.description = (
    Description('Retrieve segmentation tile PNG image for a given image item.')
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
#@loadmodel(map={'item_id': 'item'}, model='item', level=AccessType.READ)
def fifHandler(item_id, params, **kwargs):
    # can't use "loadmodel", as the requesting user may actually be the server
    #   in "image_processing.fillImageGeoJSON", which doesn't send credentials
    item = ModelImporter.model('item').load(item_id, force=True)

    zsplit = cherrypy.url().split('fif/')

    if len(zsplit) > 1:
        image_file = ModelImporter.model('image', 'isic_archive').multiresolutionFile(item)

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
