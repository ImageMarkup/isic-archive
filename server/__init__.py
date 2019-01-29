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

import six

from girder import events
from girder.api.v1 import resource
from girder.utility import mail_utils
from girder.utility.plugin_utilities import registerPluginWebroot
from girder.utility.server import staticFile
from girder.utility.webroot import WebrootBase

from . import api
# Import settings for side effects
from . import settings  # noqa: F401
from .provision_utility import provisionDatabase


def onDescribeResource(event):
    # Patch a bug with how Girder's Swagger descriptions work with Vagrant
    # port forwarding and Nginx proxies
    # This is fundamentally a problem with "rest.getApiUrl"
    describeResponse = event.info['returnVal']
    # TODO: get this from the server config or the request
    describeResponse['basePath'] = '/api/v1'


def clearRouteDocs():
    from girder.api.docs import routes

    # Preserve some upstream operations for user lifecycle management
    savedRoutes = {}
    for routeMethod, routePath in {
        ('GET', '/user/authentication'),  # log in by password
        ('DELETE', '/user/authentication'),  # log out
        ('GET', '/user/me'),  # personal info on the current user
        ('POST', '/user'),  # personal info on the current user
        ('GET', '/oauth/provider'),  # initiate an OAuth2 workflow for login / registration
        ('PUT', '/user/{id}'),  # change personal info
        ('PUT', '/user/password'),  # change password
        ('PUT', '/user/password/temporary'),  # initiate email reset of forgotten password
        ('GET', '/user/password/temporary/{id}'),  # complete email reset of forgotten password
        ('POST', '/user/verification'),  # resend an email verification message
    }:
        # The [0] element of the routePath split is '', since it starts with a '/'
        routeResource = routePath.split('/')[1]
        try:
            routeOperation = routes[routeResource][routePath][routeMethod]
        except KeyError:
            continue
        savedRoutes[(routeResource, routePath, routeMethod)] = routeOperation

    routes.clear()

    for (routeResource, routePath, routeMethod), routeOperation in six.viewitems(savedRoutes):
        routes[routeResource][routePath][routeMethod] = routeOperation


def load(info):
    # set the title of the HTML pages
    info['serverRoot'].updateHtmlVars({'title': 'ISIC Archive'})

    # add event listeners
    events.bind('rest.get.describe/:resource.after',
                'onDescribeResource', onDescribeResource)

    # add custom model searching
    resource.allowedSearchTypes.update({
        'image.isic_archive',
        'study.isic_archive',
    })

    # register licenses for template usage
    mail_utils.addTemplateDirectory(
        os.path.join(info['pluginRootDir'], 'server', 'license_templates'),
        prepend=True)

    externalWebroot = WebrootBase(os.path.join(info['pluginRootDir'], 'server', 'webroot.mako'))
    externalWebroot.updateHtmlVars({
        'apiRoot': '/api/v1',
        'staticRoot': '/static',
        'title': 'ISIC Archive'
    })
    registerPluginWebroot(externalWebroot, info['name'])

    integrationWebroot = WebrootBase(os.path.join(
        info['pluginRootDir'], 'server', 'webroot_integration.mako'))
    integrationWebroot.updateHtmlVars(externalWebroot.vars)
    registerPluginWebroot(integrationWebroot, info['name'] + '_integration')

    # add static file serving
    info['config']['/uda'] = {
        'tools.staticdir.on': 'True',
        'tools.staticdir.dir': os.path.join(info['pluginRootDir'], 'custom')
    }

    # add dynamic root routes
    # root endpoints -> where a user may go and expect a UI
    class Root(object):
        pass
    legacyWebroot = Root()
    legacyWebroot.segment = staticFile(
        os.path.join(info['pluginRootDir'], 'custom', 'phase1.html'))
    registerPluginWebroot(legacyWebroot, 'markup')

    # create all necessary users, groups, collections, etc
    provisionDatabase()

    # add api routes
    # remove docs for default Girder API, to simplify page
    clearRouteDocs()

    # Customize API docs template
    baseTemplateFilename = info['apiRoot'].templateFilename
    info['apiRoot'].updateHtmlVars({
        'baseTemplateFilename': baseTemplateFilename
    })
    templatePath = os.path.join(info['pluginRootDir'], 'server', 'isic_api_docs.mako')
    info['apiRoot'].setTemplatePath(templatePath)

    # TODO: nest these under a "/isic" path?
    info['apiRoot'].annotation = api.AnnotationResource()
    info['apiRoot'].dataset = api.DatasetResource()
    info['apiRoot'].image = api.ImageResource()
    info['apiRoot'].redirects = api.RedirectsResource()
    info['apiRoot'].segmentation = api.SegmentationResource()
    info['apiRoot'].study = api.StudyResource()
    info['apiRoot'].task = api.TaskResource()
    api.attachUserApi(info['apiRoot'].user)
