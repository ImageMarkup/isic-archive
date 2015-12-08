#!/usr/bin/env python
# -*- coding: utf-8 -*-

import cherrypy

from girder.api import access
from girder.api.rest import Resource, RestException, loadmodel
from girder.api.describe import Description, describeRoute
from girder.constants import AccessType

from ..image_processing import fillImageGeoJSON


class ImageResource(Resource):
    def __init__(self,):
        super(ImageResource, self).__init__()
        self.resourceName = 'image'

        self.route('GET', (), self.find)
        self.route('GET', (':id',), self.getImage)
        self.route('GET', (':id', 'thumbnail'), self.thumbnail)

        # TODO: change to GET
        self.route('POST', (':id', 'segment-boundary'), self.segmentBoundary)


    @describeRoute(
        Description('Return a list of lesion images.')
        .pagingParams(defaultSort='lowerName')
        .param('datasetId', 'The ID of the dataset to use.', required=True)
        .errorResponse()
    )
    @access.public
    def find(self, params):
        self.requireParams('datasetId', params)
        user = self.getCurrentUser()
        limit, offset, sort = self.getPagingParameters(params, 'lowerName')

        dataset = self.model('dataset', 'isic_archive').load(
            id=params['datasetId'], user=user, level=AccessType.READ, exc=True)
        return [
            {
                field: image[field]
                for field in
                self.model('image', 'isic_archive').summaryFields
            }
            for image in
            self.model('dataset', 'isic_archive').childImages(
                dataset, limit=limit, offset=offset, sort=sort)
        ]


    @describeRoute(
        Description('Return an image\'s details.')
        .param('id', 'The ID of the image.', paramType='path')
        .errorResponse('ID was invalid.')
    )
    @access.public
    @loadmodel(model='image', plugin='isic_archive', level=AccessType.READ)
    def getImage(self, image, params):
        return self.model('image', 'isic_archive').filter(
            image, self.getCurrentUser())


    @describeRoute(
        Description('Return an image\'s thumbnail.')
        .param('id', 'The ID of the image.', paramType='path')
        .errorResponse('ID was invalid.')
    )
    @access.cookie
    @access.public
    @loadmodel(model='image', plugin='isic_archive', level=AccessType.READ)
    def thumbnail(self, image, params):
        width = int(params.get('width', 256))
        thumbnail_url = self.model('image', 'isic_archive').tileServerURL(
            image, width=width)
        raise cherrypy.HTTPRedirect(thumbnail_url, status=307)


    @describeRoute(
        Description('Return an image\'s boundary segmentation.')
        # .responseClass('Image')
        .param('id', 'The ID of the image.', paramType='path')
        .errorResponse('ID was invalid.')
    )
    @access.user
    @loadmodel(model='image', plugin='isic_archive', level=AccessType.READ)
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
