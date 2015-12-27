#!/usr/bin/env python
# -*- coding: utf-8 -*-

from six import BytesIO

import cherrypy
from PIL import Image as PIL_Image, ImageDraw as PIL_ImageDraw

from girder.api import access
from girder.api.rest import Resource, loadmodel
from girder.api.describe import Description, describeRoute
from girder.constants import AccessType, SortDir


class SegmentationResource(Resource):
    def __init__(self,):
        super(SegmentationResource, self).__init__()
        self.resourceName = 'segmentation'

        self.route('GET', (), self.find)
        # self.route('POST', (), self.createSegmentation)
        self.route('GET', (':id',), self.getSegmentation)
        self.route('GET', (':id', 'thumbnail'), self.thumbnail)

        self.route('GET', (':id', 'superpixels'), self.getSuperpixels)


    @describeRoute(
        Description('List the segmentations for an image.')
        .param('imageId', 'The ID of the image.', paramType='query')
        .errorResponse('ID was invalid.')
    )
    @access.public
    def find(self, params):
        self.requireParams(('imageId',), params)

        image = self.model('image', 'isic_archive').load(
            params['imageId'], level=AccessType.READ,
            user=self.getCurrentUser(), exc=True)

        return list(self.model('segmentation', 'isic_archive').find(
            query={'imageId': image['_id']},
            sort=[('created', SortDir.DESCENDING)],
            fields=['_id', 'skill', 'created']
        ))


    @describeRoute(
        Description('Add a segmentation to an image.')
        .param('image_id', 'The ID of the image.', paramType='body')
        .errorResponse('ID was invalid.')
    )
    @access.user
    @loadmodel(model='image', plugin='isic_archive', level=AccessType.READ)
    def createSegmentation(self, image, params):
        pass


    @describeRoute(
        Description('Get a segmentation for an image.')
        .param('id', 'The ID of the segmentation.', paramType='path')
        .errorResponse('ID was invalid.')
    )
    @access.public
    @loadmodel(model='segmentation', plugin='isic_archive')
    def getSegmentation(self, segmentation, params):
        # TODO: convert this to make Segmentation use an AccessControlMixin
        self.model('image', 'isic_archive').load(
            segmentation['imageId'], level=AccessType.READ,
            user=self.getCurrentUser(), exc=True)

        segmentation['creator'] = self.model('user').load(
            segmentation.pop('creatorId'),
            force=True, exc=True,
            fields={'_id', 'login', 'firstName', 'lastName'})

        # Deal with a bug in Girder
        # TODO: Remove this
        import six
        segmentation['creator'] = {
            k: v
            for k, v in six.viewitems(segmentation['creator'])
            if k in {'_id', 'login', 'firstName', 'lastName'}
        }

        return segmentation


    @describeRoute(
        Description('Get a thumbnail, showing a segmentation.')
        .param('id', 'The ID of the segmentation.', paramType='path')
        .param('width', 'The desired width for the thumbnail.',
               paramType='query', required=False)
        .errorResponse('ID was invalid.')
    )
    @access.cookie
    @access.public
    @loadmodel(model='segmentation', plugin='isic_archive')
    def thumbnail(self, segmentation, params):
        image = self.model('image', 'isic_archive').load(
            segmentation['imageId'], level=AccessType.READ,
            user=self.getCurrentUser(), exc=True)

        width = int(params.get('width', 256))

        image_data = self.model('image', 'isic_archive').imageData(image)
        pil_image_data = PIL_Image.fromarray(image_data)
        pil_draw = PIL_ImageDraw.Draw(pil_image_data)
        pil_draw.line(
            list(map(tuple, segmentation['lesionBoundary']['geometry']['coordinates'][0])),
            fill=(0, 255, 0),  # TODO: make color an option
            width=5
        )

        output_image_data = BytesIO()
        factor = pil_image_data.size[0] / float(width)
        pil_image_data.resize((
            int(pil_image_data.size[0] / factor),
            int(pil_image_data.size[1] / factor)
        )).save(output_image_data, format='jpeg')

        cherrypy.response.headers['Content-Type'] = 'image/jpeg'
        return output_image_data.getvalue


    @describeRoute(
        Description('Get the superpixels for this segmentation, as a'
                    ' PNG-encoded label map.')
        .param('id', 'The ID of the segmentation.', paramType='path')
        .errorResponse('ID was invalid.')
    )
    @access.cookie
    @access.public
    @loadmodel(model='segmentation', plugin='isic_archive')
    def getSuperpixels(self, segmentation, params):
        Segmentation = self.model('segmentation', 'isic_archive')
        superpixels_file = Segmentation.superpixelsFile(segmentation)
        return self.model('file').download(superpixels_file, headers=True)
