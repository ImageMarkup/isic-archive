#!/usr/bin/env python
# -*- coding: utf-8 -*-

###############################################################################
#  Copyright Kitware Inc.
#
#  Licensed under the Apache License, Version 2.0 ( the "License" );
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
###############################################################################

import os

from girder import events
from girder.api.rest import getCurrentUser
from girder.api.v1 import resource
from girder.constants import SettingKey, PACKAGE_DIR, STATIC_ROOT_DIR
from girder.models.model_base import ValidationException
from girder.utility.model_importer import ModelImporter
from girder.utility.server import staticFile
from girder.utility.webroot import WebrootBase

from . import constants
from . import api
from .provision_utility import initialSetup, onUserCreated


class Webroot(WebrootBase):
    """
    The webroot endpoint simply serves the main index HTML file.
    """
    def __init__(self, templatePath=None):
        if not templatePath:
            templatePath = os.path.join(
                PACKAGE_DIR, os.pardir, 'plugins', 'isic_archive', 'server',
                'webroot.mako')
        super(Webroot, self).__init__(templatePath)

        self.vars = {
            'apiRoot': '/api/v1',
            'staticRoot': '/static',
            'title': 'ISIC Archive'
            }

    def _renderHTML(self):
        self.vars['pluginCss'] = []
        self.vars['pluginJs'] = []
        builtDir = os.path.join(
            STATIC_ROOT_DIR, 'clients', 'web', 'static', 'built', 'plugins')
        self.vars['plugins'] = ModelImporter.model('setting').get(
            SettingKey.PLUGINS_ENABLED, ())
        for plugin in self.vars['plugins']:
            if os.path.exists(os.path.join(builtDir, plugin, 'plugin.min.css')):
                self.vars['pluginCss'].append(plugin)
            if os.path.exists(os.path.join(builtDir, plugin, 'plugin.min.js')):
                self.vars['pluginJs'].append(plugin)

        return super(Webroot, self)._renderHTML()


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


def onGetItem(event):
    itemResponse = event.info['returnVal']

    # Hide the 'originalFilename' metadata on Images from non-site admins
    if 'originalFilename' in itemResponse.get('meta', {}):
        currentUser = getCurrentUser()
        if not (currentUser and currentUser['admin']):
            del itemResponse['meta']['originalFilename']


def onDescribeResource(event):
    # Patch a bug with how Girder's Swagger descriptions work with Vagrant
    # port forwarding and Nginx proxies
    # This is fundamentally a problem with "rest.getApiUrl"
    describeResponse = event.info['returnVal']
    # TODO: get this from the server config or the request
    describeResponse['basePath'] = '/api/v1'


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
    events.bind('model.user.save.created', 'onUserCreated', onUserCreated)
    events.bind('rest.get.item/:id.after', 'onGetItem', onGetItem)
    events.bind('rest.get.describe/:resource.after',
                'onDescribeResource', onDescribeResource)
    ModelImporter.model('setting').set(SettingKey.USER_DEFAULT_FOLDERS, 'none')

    # add custom model searching
    resource.allowedSearchTypes.update({
        'image.isic_archive',
        'featureset.isic_archive',
        'study.isic_archive',
    })

    # create all necessary users, groups, collections, etc
    initialSetup()

    # add static file serving
    app_base = os.path.join(os.curdir, os.pardir)
    app_path = os.path.join(
        app_base, 'girder', 'plugins', 'isic_archive', 'custom')

    info['config']['/uda'] = {
        'tools.staticdir.on': 'True',
        'tools.staticdir.dir': app_path
    }

    # Move girder app to /girder, serve isic_archive app from /
    info['serverRoot'], info['serverRoot'].girder = (
        Webroot(), info['serverRoot'])
    info['serverRoot'].api = info['serverRoot'].girder.api

    # add dynamic root routes
    # root endpoints -> where a user may go and expect a UI
    class Root(object):
        pass
    info['serverRoot'].uda = Root()

    info['serverRoot'].uda.gallery = staticFile(
        os.path.join(info['pluginRootDir'], 'custom', 'gallery.html'))

    info['serverRoot'].uda.segment = staticFile(
        os.path.join(info['pluginRootDir'], 'custom', 'phase1.html'))

    info['serverRoot'].uda.annotate = staticFile(
        os.path.join(info['pluginRootDir'], 'custom', 'phase2.html'))

    # add api routes
    # remove docs for default Girder API, to simplify page
    clearRouteDocs()

    # TODO: nest these under a "/isic" path?
    info['apiRoot'].annotation = api.AnnotationResource()
    info['apiRoot'].dataset = api.DatasetResource()
    info['apiRoot'].featureset = api.FeaturesetResource()
    info['apiRoot'].image = api.ImageResource()
    info['apiRoot'].segmentation = api.SegmentationResource()
    info['apiRoot'].study = api.StudyResource()
    info['apiRoot'].task = api.TaskResource()
    api.attachUserApi()
