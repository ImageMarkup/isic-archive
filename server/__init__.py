#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

import cherrypy
from girder import events
from girder.models.model_base import ValidationException
from girder.utility.server import _StaticFileRoute

from . import constants
from .annotate import FillHandler
from . import api
from .image_utility import zoomifyhandler, thumbnailhandler, fifHandler, segmentationSourceHandler, segmentationTileHandler
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


def validateSettings(event):
    key, val = event.info['key'], event.info['value']

    if key == constants.PluginSettings.DEMO_MODE:
        if not isinstance(val, bool):
            raise ValidationException(
                'Demo mode must be provided as a boolean.', 'value')
        event.preventDefault().stopPropagation()


def load(info):
    # set the title of the HTML pages
    info['serverRoot'].updateHtmlVars({'title': 'ISIC Archive'})

    # add event listeners
    # note, 'model.setting.validate' must be bound before initialSetup is called
    events.bind('model.setting.validate', 'uda', validateSettings)
    events.bind('data.process', 'uploadHandler', uploadHandler)
    events.bind('model.user.save.created', 'onUserCreated', onUserCreated)

    # create all necessary users, groups, collections, etc
    initialSetup(info)


    # add static file serving
    app_base = os.path.join(os.curdir, os.pardir)
    app_path = os.path.join(app_base, 'girder', 'plugins', 'isic_archive', 'custom')

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
    info['apiRoot'].item.route('GET', (':item_id', 'thumbnail'), thumbnailhandler)

    # "/api/v1/item/:id/segmentationSource" -> returns the png segmentation (index map as alpha channel)
    info['apiRoot'].item.route('GET', (':item_id', 'segmentationSource'), segmentationSourceHandler)
    # "/api/v1/item/:id/segmentationTiles"
    info['apiRoot'].item.route('GET', (':item_id', 'segmentationTiles'), segmentationTileHandler)

    # "/api/v1/item/:id/zoomify/:p1" -> returns a zoomify xml if available
    info['apiRoot'].item.route('GET', (':item_id', 'zoomify', ':p1'), zoomifyhandler)
    # "/api/v1/item/:id/zoomify/:p1/:p2"
    info['apiRoot'].item.route('GET', (':item_id', 'zoomify', ':p1', ':p2'), zoomifyhandler)

    # "/api/v1/item/:id/fif/:fifparams" -> returns the IIP FIF endpoint for an item
    info['apiRoot'].item.route('GET', (':item_id', 'fif', ':fifparams'), fifHandler)

    # TODO: nest these under a "/isic" path
    info['apiRoot'].annotation = api.AnnotationResource(info['pluginRootDir'])
    info['apiRoot'].featureset = api.FeaturesetResource()
    info['apiRoot'].study = api.StudyResource()
