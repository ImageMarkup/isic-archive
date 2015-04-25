#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

import cherrypy
from girder import events
from girder.utility.server import _StaticFileRoute

from .annotate import FillHandler
from .image_utility import zoomifyhandler, thumbnailhandler, fifHandler, annotationHandler, segmentationSourceHandler, segmentationTileHandler
from .provision_utility import initialSetup, onUserCreated
from .task_utility import UDAResource, TaskHandler
from .upload import uploadHandler


class StaticRouteWithId(_StaticFileRoute):
    """
    This creates a static route with an optional nonfunctional "/:id" variable
    path component at the end.
    """
    @cherrypy.popargs('id')
    def GET(self, id=None):
        return super(StaticRouteWithId, self).GET()


def load(info):
    # create all necessary users, groups, collections, etc
    initialSetup()


    # add static file serving
    app_base = os.path.join(os.curdir, os.pardir)
    app_path = os.path.join(app_base, 'girder', 'plugins', 'uda', 'custom')

    info['config']['/uda'] = {
        'tools.staticdir.on': 'True',
        'tools.staticdir.dir': app_path
    }


    # add dynamic root routes
    # root endpoints -> where a user may go and expect a UI
    class Root(object):
        pass
    info['serverRoot'].uda = Root()

    # "/uda/gallery/:folderId" -> returns a single page gallery
    info['serverRoot'].uda.gallery = StaticRouteWithId(os.path.join(info['pluginRootDir'], 'custom', 'gallery.html'))

    # "uda/qc/:folderId" -> returns a QC page where user can move images to
    info['serverRoot'].uda.qc = StaticRouteWithId(os.path.join(info['pluginRootDir'], 'custom', 'qc.html'))

    # "uda/view/:itemId" -> simple zoomable viewer for an image
    # TODO

    # "/uda/task" -> redirects to appropriate task view for the user
    info['serverRoot'].uda.task = TaskHandler(info['pluginRootDir'])

    # "/uda/annotator/:id" -> the reconfigurable image annotator
    info['serverRoot'].uda.annotate = StaticRouteWithId(os.path.join(info['pluginRootDir'], 'custom', 'annotate.html'))

    # "/uda/map/:id"
    info['serverRoot'].uda.map = StaticRouteWithId(os.path.join(info['pluginRootDir'], 'custom', 'map.html'))

    # "/uda/fill/:id" (POST only)
    info['serverRoot'].uda.fill = FillHandler()


    # add api routes
    info['apiRoot'].uda = UDAResource(info['pluginRootDir'])

    # "/api/v1/item/:id/thumbnail" -> returns a thumbnail of the image
    info['apiRoot'].item.route('GET', (':id', 'thumbnail'), thumbnailhandler)

    # "/api/v1/item/:id/annotation" -> returns the json annotation
    info['apiRoot'].item.route('GET', (':id', 'annotation'), annotationHandler)

    # "/api/v1/item/:id/segmentationSource" -> returns the png segmentation (index map as alpha channel)
    info['apiRoot'].item.route('GET', (':id', 'segmentationSource'), segmentationSourceHandler)
    # "/api/v1/item/:id/segmentationTiles"
    info['apiRoot'].item.route('GET', (':id', 'segmentationTiles'), segmentationTileHandler)

    # "/api/v1/item/:id/zoomify/:p1" -> returns a zoomify xml if available
    info['apiRoot'].item.route('GET', (':id', 'zoomify', ':p1'), zoomifyhandler)
    # "/api/v1/item/:id/zoomify/:p1/:p2"
    info['apiRoot'].item.route('GET', (':id', 'zoomify', ':p1', ':p2'), zoomifyhandler)

    # "/api/v1/item/:id/fif/:fifparams" -> returns the IIP FIF endpoint for an item
    info['apiRoot'].item.route('GET', (':id', 'fif', ':fifparams'), fifHandler)


    # add event listeners
    events.bind('data.process', 'uploadHandler', uploadHandler)

    events.bind('model.user.save.created', 'onUserCreated', onUserCreated)
