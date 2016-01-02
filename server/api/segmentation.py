#!/usr/bin/env python
# -*- coding: utf-8 -*-

import cherrypy

from girder.api import access
from girder.api.rest import Resource, loadmodel, rawResponse
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

        userSummaryFields = ['_id', 'login', 'firstName', 'lastName']
        segmentation['creator'] = self.model('user').load(
            segmentation.pop('creatorId'),
            force=True, exc=True,
            fields=userSummaryFields)

        # Deal with a bug in Girder
        # TODO: Remove this
        import six
        segmentation['creator'] = {
            k: v
            for k, v in six.viewitems(segmentation['creator'])
            if k in userSummaryFields
        }

        return segmentation


    @describeRoute(
        Description('Get a thumbnail, showing a segmentation.')
        .param('id', 'The ID of the segmentation.', paramType='path')
        .param('width', 'The desired width for the thumbnail.',
               paramType='query', required=False, default=256)
        .errorResponse('ID was invalid.')
    )
    @access.cookie
    @access.public
    @rawResponse
    @loadmodel(model='segmentation', plugin='isic_archive')
    def thumbnail(self, segmentation, params):
        # TODO: convert this to make Segmentation use an AccessControlMixin
        image = self.model('image', 'isic_archive').load(
            segmentation['imageId'], level=AccessType.READ,
            user=self.getCurrentUser(), exc=True)

        width = int(params.get('width', 256))

        thumbnail_image_data = self.model('segmentation', 'isic_archive').boundaryThumbnail(
            segmentation, image, width)

        cherrypy.response.headers['Content-Type'] = 'image/jpeg'
        return thumbnail_image_data.getvalue()


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
