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

import cherrypy

from girder.api import access

from .base import IsicResource


class RedirectsResource(IsicResource):
    def __init__(self):
        super(RedirectsResource, self).__init__()
        self.resourceName = 'redirects'

        self.route('GET', ('uploadBatch',), self.redirectUploadBatch)
        self.route('GET', ('literature',), self.redirectLiterature)
        self.route('GET', ('registerMetadata',), self.redirectRegisterMetadata)
        self.route('GET', ('applyMetadata',), self.redirectApplyMetadata)

    def _doRedirect(self, url):
        exc = cherrypy.HTTPRedirect(url, status=307)
        # "cherrypy.HTTPRedirect" will convert all URLs to be absolute and
        # external; however, the hostname for external URLs may not be deduced
        # correctly in all environments, so keep the url as-is
        exc.urls = [url]
        raise exc

    @access.public
    def redirectUploadBatch(self, params):
        self._doRedirect('/#dataset/upload/batch')

    @access.public
    def redirectLiterature(self, params):
        self._doRedirect('/#literature')

    @access.public
    def redirectRegisterMetadata(self, params):
        self._doRedirect('/#dataset/%s/metadata/register' % str(params.get('datasetId', '')))

    @access.public
    def redirectApplyMetadata(self, params):
        self._doRedirect('/#dataset/%s/metadata/apply' % str(params.get('datasetId', '')))
