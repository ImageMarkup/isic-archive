#!/usr/bin/env python
# -*- coding: utf-8 -*-

import collections
import os

import cv2
import numpy
import requests
from requests.packages.urllib3.util import Url

from girder.api.rest import getUrlParts
from girder.models.model_base import GirderException
from girder.models.item import Item


class Image(Item):

    def multiresolutionFile(self, image):
        return self.model('file').findOne({
            'itemId': image['_id'],
            'name': image['meta']['convertedFilename']
        })


    def tileServerURL(self, image, params=None):
        image_file = self.multiresolutionFile(image)
        assetstore = self.model('assetstore').load(image_file['assetstoreId'])
        file_path = os.path.join(assetstore['root'], image_file['path'])

        # the ordering of query string parameters to IIP matters
        query_params = collections.OrderedDict()
        # FIF seems to need to come first
        query_params['FIF'] = file_path
        query_params['CVT'] = 'jpeg'
        if params:
            query_params.update(params)

        # TODO: this won't work if the server's DNS doesn't know its own canonical hostname
        current_location = getUrlParts()
        url = Url(
            scheme=current_location.scheme,
            host=current_location.netloc,
            port=None,
            path='/fcgi-bin/iipsrv.fcgi',
            query='&'.join('%s=%s' % item for item in query_params.viewitems())
        )
        return url.url


    def binaryImageJpeg(self, image):
        image_server_url = self.tileServerURL(image)
        try:
            response = requests.get(image_server_url)
            response.raise_for_status()
        except requests.RequestException:
            raise GirderException('Tile server unavailable.')
        image_data = numpy.fromstring(response.content, dtype=numpy.uint8)
        return image_data


    def binaryImageRaw(self, image):
        jpeg_image_data = self.binaryImageJpeg(image)
        raw_image_data = cv2.imdecode(jpeg_image_data, cv2.CV_LOAD_IMAGE_COLOR)
        return raw_image_data


    def validate(self, doc):
        # TODO: implement
        # raise ValidationException
        return Item.validate(self, doc)
