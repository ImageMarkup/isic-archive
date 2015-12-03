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

from .. import constants


class Image(Item):

    def createImage(self, creator, parentFolder):
        new_isic_id = self.model('setting').get(
            constants.PluginSettings.MAX_ISIC_ID, default=-1) + 1

        image = self.createItem(
            name='ISIC_%07d' % new_isic_id,
            creator=creator,
            folder=parentFolder,
            description=''
        )
        self.setMetadata(image, {
            'clinical': {}
        })

        self.model('setting').set(
            constants.PluginSettings.MAX_ISIC_ID, new_isic_id)

        return image


    def multiresolutionFile(self, image):
        return self.model('file').findOne({
            'itemId': image['_id'],
            'name': image['meta']['convertedFilename']
        })


    def tileServerURL(self, image, width=None):
        image_file = self.multiresolutionFile(image)
        assetstore = self.model('assetstore').load(image_file['assetstoreId'])
        file_path = os.path.join(assetstore['root'], image_file['path'])

        # the ordering of query string parameters to IIP critically matters
        query_params = collections.OrderedDict()
        query_params['FIF'] = file_path
        if width:
            query_params['WID'] = width
        query_params['CVT'] = 'jpeg'

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
