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

import json

import cherrypy
import six

from girder.api.rest import Resource, RestException


class IsicResource(Resource):
    def _decodeParams(self, params):
        """
        Decode POSTed or PUTed JSON parameters, from either
        "application/x-www-form-urlencoded" or "application/json" bodies.
        :param params: The "params" parameter from a Resource route handler.
        :type params: dict
        :return: The decoded parameters.
        :rtype: dict
        """
        if cherrypy.request.headers.get('Content-Type', '').split(';')[0] == 'application/json':
            decodedParams = self.getBodyJson()
            if not isinstance(decodedParams, dict):
                raise RestException('JSON content should be an object at the top level.')
        else:
            decodedParams = {}
            for field, value in six.viewitems(params):
                try:
                    decodedValue = json.loads(value)
                except ValueError:
                    # Assume this was just a simple string; invalid JSON should
                    # be caught later by type checking validation
                    decodedValue = value
                decodedParams[field] = decodedValue
        return decodedParams
