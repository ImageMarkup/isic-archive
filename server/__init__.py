#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

from girder import events
from girder.constants import SettingKey
from girder.models.model_base import ValidationException
from girder.utility.model_importer import ModelImporter
from girder.utility.server import staticFile

from . import constants
from . import api
from .provision_utility import initialSetup, onUserCreated
from .task_utility import UDAResource, TaskHandler
from .upload import uploadHandler


def validateSettings(event):
    key, val = event.info['key'], event.info['value']

    if key == constants.PluginSettings.DEMO_MODE:
        if not isinstance(val, bool):
            raise ValidationException(
                'Demo mode must be provided as a boolean.', 'value')
        event.preventDefault().stopPropagation()

    if key == constants.PluginSettings.MAX_ISIC_ID:
        # TODO: can we disable this from being set via the HTTP API?
        if not isinstance(val, int):
            raise ValidationException(
                'Maximum ISIC ID must be provided as an integer.', 'value')
        event.preventDefault().stopPropagation()


def clearRouteDocs():
    from girder.api.docs import routes
    # preserve the user token login operation
    user_auth_ops = routes['user']['/user/authentication']
    routes.clear()
    routes['user']['/user/authentication'] = user_auth_ops


def load(info):
    # set the title of the HTML pages
    info['serverRoot'].updateHtmlVars({'title': 'ISIC Archive'})

    # add event listeners
    # note, 'model.setting.validate' must be bound before initialSetup is called
    events.bind('model.setting.validate', 'isic', validateSettings)
    events.bind('data.process', 'uploadHandler', uploadHandler)
    events.bind('model.user.save.created', 'onUserCreated', onUserCreated)
    ModelImporter.model('setting').set(SettingKey.USER_DEFAULT_FOLDERS, 'none')

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

    # "/uda/gallery" -> returns a single page gallery
    info['serverRoot'].uda.gallery = staticFile(os.path.join(info['pluginRootDir'], 'custom', 'gallery.html'))

    # "/uda/task" -> redirects to appropriate task view for the user
    info['serverRoot'].uda.task = TaskHandler(info['pluginRootDir'])

    # "/uda/annotator/:id" -> the reconfigurable image annotator
    info['serverRoot'].uda.annotate = staticFile(os.path.join(info['pluginRootDir'], 'custom', 'phase1.html'))

    # "/uda/map/:id"
    info['serverRoot'].uda.map = staticFile(os.path.join(info['pluginRootDir'], 'custom', 'phase2.html'))


    # add api routes
    # remove docs for default Girder API, to simplify page
    clearRouteDocs()

    info['apiRoot'].uda = UDAResource(info['pluginRootDir'])

    # TODO: nest these under a "/isic" path
    info['apiRoot'].annotation = api.AnnotationResource(info['pluginRootDir'])
    info['apiRoot'].dataset = api.DatasetResource()
    info['apiRoot'].featureset = api.FeaturesetResource()
    info['apiRoot'].image = api.ImageResource()
    info['apiRoot'].segmentation = api.SegmentationResource()
    info['apiRoot'].study = api.StudyResource()
