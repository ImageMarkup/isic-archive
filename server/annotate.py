__author__ = 'stonerri'


from girder.utility.model_importer import ModelImporter
from girder.api.describe import Description
import cherrypy
import os
import datetime
from model_utility import *

from image_processing import *


class AnnotateHandler(object):
    exposed = True
    def __init__(self):
        pass

    # this line will map the first argument after / to the 'id' parameter
    # for example, a GET request to the url:
    # http://localhost:8000/items/
    # will call GET with id=None
    # and a GET request like this one: http://localhost:8000/items/1
    # will call GET with id=1
    # you can map several arguments using:
    # @cherrypy.propargs('arg1', 'arg2', 'argn')
    # def GET(self, arg1, arg2, argn)

    @cherrypy.popargs('id')
    def GET(self, id=None):

        app_base = os.path.join(os.curdir, os.pardir)
        qc_app_path = os.path.join(app_base, 'udaapp')
        gallery_html = os.path.abspath(os.path.join(qc_app_path, u'annotate.html'))

        fid = open(gallery_html, 'r')
        gallery_content = fid.read()
        fid.close()

        return gallery_content




    # HTML5
    def OPTIONS(self):
        cherrypy.response.headers['Access-Control-Allow-Credentials'] = True
        cherrypy.response.headers['Access-Control-Allow-Origin'] = cherrypy.request.headers['ORIGIN']
        cherrypy.response.headers['Access-Control-Allow-Methods'] = 'POST'
        cherrypy.response.headers['Access-Control-Allow-Headers'] = cherrypy.request.headers['ACCESS-CONTROL-REQUEST-HEADERS']







class FillHandler(object):
    exposed = True
    def __init__(self):
        pass

    @cherrypy.popargs('id')
    def POST(self, id=None):

        post_body = cherrypy.request.body.read()

        import json
        params = json.loads(post_body)
        results = fillImageGeoJSON(params)

        return json.dumps(results)


class SegmentationHandler(object):
    exposed = True
    def __init__(self):
        pass

    @cherrypy.popargs('id')
    def POST(self, id=None):

        post_body = cherrypy.request.body.read()

        import json
        params = json.loads(post_body)
        results = segmentImage(params)

        return json.dumps(results)


