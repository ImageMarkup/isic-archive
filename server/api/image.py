#!/usr/bin/env python
# -*- coding: utf-8 -*-

import cherrypy

from girder.api import access
from girder.api.rest import Resource, RestException, loadmodel
from girder.api.describe import Description
from girder.constants import AccessType

from ..image_processing import fillImageGeoJSON


class ImageResource(Resource):
    def __init__(self,):
        super(ImageResource, self).__init__()
        self.resourceName = 'image'

        self.route('GET', (), self.find)
        self.route('GET', (':id', 'thumbnail'), self.thumbnail)

        # TODO: change to GET
        self.route('POST', (':id', 'segment-boundary'), self.segmentBoundary)


    @access.public
    def find(self, params):
        user = self.getCurrentUser()
        limit, offset, sort = self.getPagingParameters(params, 'lowerName')

        if 'datasetId' in params:
            dataset = self.model('dataset', 'isic_archive').load(
                id=params['datasetId'], user=user, level=AccessType.READ, exc=True)

            images = self.model('dataset', 'isic_archive').childImages(
                dataset, limit=limit, offset=offset, sort=sort)
        else:
            # TODO: maybe make datasetId actually required and raise an Exception

            # TODO: only list images from datasets we have access to
            images = self.model('image', 'isic_archive').find(
                limit=limit, offset=offset, sort=sort)

        return [self.model('image', 'isic_archive').filter(image, user)
                for image in images]

    find.description = (
        Description('Return a list of lesion images.')
        .pagingParams(defaultSort='name')
        .param('datasetId', 'The ID of the dataset to use.', required=True)
        .errorResponse())


    @access.public
    @loadmodel(model='item', map={'id': 'image'}, level=AccessType.READ)
    def thumbnail(self, image, params):
        width = int(params.get('width', 256))
        thumbnail_url = self.model('image', 'isic_archive').tileServerURL(image, width=width)
        raise cherrypy.HTTPRedirect(thumbnail_url, status=307)

    thumbnail.cookieAuth = True
    thumbnail.description = (
        Description('Retrieve the thumbnail for a given image item.')
        .param('item_id', 'The item ID', paramType='path')
        .errorResponse())


    @access.user
    @loadmodel(model='item', map={'id': 'image'}, level=AccessType.READ)
    def segmentBoundary(self, image, params):
        body_json = self.getBodyJson()
        self.requireParams(('seed', 'tolerance'), body_json)

        # validate parameters
        seed_point = body_json['seed']
        if not (
            isinstance(seed_point, list) and
            len(seed_point) == 2 and
            all(isinstance(value, int) for value in seed_point)
        ):
            raise RestException('Submitted "seed" must be a coordinate pair.')

        tolerance = body_json['tolerance']
        if not isinstance(tolerance, int):
            raise RestException('Submitted "tolerance" must be an integer.')

        image_data = self.model('image', 'isic_archive').binaryImageRaw(image)

        results = fillImageGeoJSON(
            image_data=image_data,
            seed_point=seed_point,
            tolerance=tolerance
        )

        return results
        # return json.dumps(results)

    segmentBoundary.description = (
        Description('Return the boundary segmentation for an image.')
        # .responseClass('Image')
        .param('id', 'The ID of the image.', paramType='path')
        .param('id', 'The ID of the image.', paramType='path')
        .errorResponse('ID was invalid.'))
