import json
from typing import Dict

import cherrypy

from girder.api.rest import Resource
from girder.exceptions import RestException


class IsicResource(Resource):
    def _decodeParams(self, params: Dict) -> Dict:
        """
        Decode POSTed or PUTed JSON parameters.

        Supports either "application/x-www-form-urlencoded" or "application/json" bodies.

        :param params: The "params" parameter from a Resource route handler.
        :return: The decoded parameters.
        """
        if cherrypy.request.headers.get('Content-Type', '').split(';')[0] == 'application/json':
            decodedParams = self.getBodyJson()
            if not isinstance(decodedParams, dict):
                raise RestException('JSON content should be an object at the top level.')
        else:
            # Return parameter unchanged
            def passthrough(param):
                return param

            decodedParams = {}
            for field, value in params.items():
                try:
                    # Decode parameter, parsing numbers as strings
                    decodedValue = json.loads(value, parse_float=passthrough, parse_int=passthrough)
                except ValueError:
                    # Assume this was just a simple string; invalid JSON should
                    # be caught later by type checking validation
                    decodedValue = value
                decodedParams[field] = decodedValue
        return decodedParams
