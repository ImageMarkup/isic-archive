#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json

import cherrypy

from .image_processing import segmentImage


class SegmentationHandler(object):
    exposed = True

    @cherrypy.popargs('id')
    def POST(self, id=None):
        post_body = cherrypy.request.body.read()
        params = json.loads(post_body)

        results = segmentImage(params)

        return json.dumps(results)
