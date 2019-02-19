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

import itertools
import os

from bson import json_util
import six

from girder import events
from girder.api.v1 import resource
from girder.utility import mail_utils

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


def onJobSave(event):
    # Patch a bug with how girder_worker's Girder task spec's 'api_url' is set
    # with Vagrant port forwarding and Nginx proxies
    # This is fundamentally a problem with "rest.getApiUrl"
    job = event.info
    if job['handler'] == 'worker_handler':
        # All girder_worker jobs have 3 absolute external URLs, which need to
        # patched; these are located at (excluding other job fields):
        # job = {
        #     'kwargs': {
        #         'inputs': {
        #             '<input_name1>': {
        #                 'mode': 'girder',
        #                 'api_url': '<external_url>'
        #             }
        #         },
        #         'outputs': {
        #             '<output_name1>': {
        #                 'mode': 'girder',
        #                 'api_url': '<external_url>'
        #             }
        #         },
        #         'jobInfo': {
        #             'url': '<external_url>'
        #         }
        #     }
        # }

        # We need to do this for all job statuses, since due to the way that
        # Job.save is overridden, the local model may be desynchronized from
        # the database after saving; this is fine, since girder_worker
        # (where it matters) will always load directly from the correct entry
        # in the database
        def replaceHost(url):
            # TODO: get this from the server config or the request
            return 'http://127.0.0.1:8080' + url[url.find('/api/v1'):]

        job['kwargs'] = json_util.loads(job['kwargs'])
        for specValue in itertools.chain(
                six.viewvalues(job['kwargs'].get('inputs', {})),
                six.viewvalues(job['kwargs'].get('outputs', {}))):
            if specValue['mode'] == 'girder':
                specValue['api_url'] = replaceHost(specValue['api_url'])
        if job['kwargs'].get('jobInfo'):
            job['kwargs']['jobInfo']['url'] = replaceHost(
                job['kwargs']['jobInfo']['url'])
        job['kwargs'] = json_util.dumps(job['kwargs'])


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
    events.bind('model.job.save', 'onJobSave', onJobSave)

    # add custom model searching
    resource.allowedSearchTypes.update({
        'image.isic_archive',
        'study.isic_archive',
    })

    # register licenses for template usage
    mail_utils.addTemplateDirectory(
        os.path.join(info['pluginRootDir'], 'server', 'license_templates'),
        prepend=True)

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
