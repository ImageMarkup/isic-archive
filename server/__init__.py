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

import six
import lxml.html
from bson import json_util
from six.moves import urllib

from girder import constants, events
from girder.api.v1 import resource
from girder.utility import mail_utils
from girder.utility.plugin_utilities import getPluginDir, registerPluginWebroot
from girder.utility.server import staticFile
from girder.utility.webroot import WebrootBase

from . import api
# Import settings for side effects
from . import settings  # noqa: F401
from .provision_utility import provisionDatabase


class Webroot(WebrootBase):
    """
    The webroot endpoint simply serves the main index HTML file.
    """
    def __init__(self, templatePath=None):
        if not templatePath:
            templatePath = os.path.join(getPluginDir(), 'isic_archive', 'server', 'webroot.mako')
        super(Webroot, self).__init__(templatePath)

        self.vars = {
            'apiRoot': '/api/v1',
            'staticRoot': '/static',
            'title': 'ISIC Archive'
        }


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
    # preserve the user token login operation
    user_auth_ops = routes['user']['/user/authentication']
    routes.clear()
    routes['user']['/user/authentication'] = user_auth_ops


def loadApiDocsTemplate():
    """
    Return upstream API docs template with description replaced by custom template.
    """
    baseTemplatePath = os.path.join(constants.PACKAGE_DIR, 'api', 'api_docs.mako')

    apiDescriptionTemplatePath = os.path.join(
        getPluginDir(), 'isic_archive', 'server', 'api_description.mako')
    with open(apiDescriptionTemplatePath) as apiDescriptionTemplateFile:
        apiDescriptionTemplate = apiDescriptionTemplateFile.read()

    # Parse upstream template and replace API description
    tree = lxml.html.parse(baseTemplatePath)
    root = tree.getroot()
    body = root.find_class('docs-body')[0]
    for child in body:
        body.remove(child)
    description = lxml.html.fragments_fromstring(apiDescriptionTemplate)
    body.extend(description)

    # Return string representation, undoing the URL encoding
    template = lxml.html.tostring(tree)
    template = urllib.parse.unquote(template)
    return template


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
        'featureset.isic_archive',
        'study.isic_archive',
    })

    # register licenses for template usage
    mail_utils.addTemplateDirectory(
        os.path.join(info['pluginRootDir'], 'server', 'license_templates'),
        prepend=True)

    registerPluginWebroot(Webroot(), info['name'])

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
    legacyWebroot.gallery = staticFile(
        os.path.join(info['pluginRootDir'], 'custom', 'gallery.html'))
    legacyWebroot.segment = staticFile(
        os.path.join(info['pluginRootDir'], 'custom', 'phase1.html'))
    legacyWebroot.annotate = staticFile(
        os.path.join(info['pluginRootDir'], 'custom', 'phase2.html'))
    registerPluginWebroot(legacyWebroot, 'markup')

    # create all necessary users, groups, collections, etc
    provisionDatabase()

    # add api routes
    # remove docs for default Girder API, to simplify page
    clearRouteDocs()

    # Customize API docs template
    try:
        info['apiRoot'].template = loadApiDocsTemplate()
    except Exception:
        # ignore and use default template
        pass

    # TODO: nest these under a "/isic" path?
    info['apiRoot'].annotation = api.AnnotationResource()
    info['apiRoot'].dataset = api.DatasetResource()
    info['apiRoot'].featureset = api.FeaturesetResource()
    info['apiRoot'].image = api.ImageResource()
    info['apiRoot'].segmentation = api.SegmentationResource()
    info['apiRoot'].study = api.StudyResource()
    info['apiRoot'].task = api.TaskResource()
    api.attachUserApi(info['apiRoot'].user)
