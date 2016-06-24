#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime

import cherrypy

from girder.api import access
from girder.api.rest import Resource, RestException, loadmodel, rawResponse
from girder.api.describe import Description, describeRoute
from girder.constants import AccessType, SortDir

from ..provision_utility import ISIC, getAdminUser


class SegmentationResource(Resource):
    def __init__(self,):
        super(SegmentationResource, self).__init__()
        self.resourceName = 'segmentation'

        self.route('GET', (), self.find)
        self.route('POST', (), self.createSegmentation)
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
    def createSegmentation(self, params):
        Segmentation = self.model('segmentation', 'isic_archive')
        Folder = self.model('folder')

        body_json = self.getBodyJson()
        self.requireParams(('imageId', 'lesionBoundary'), body_json)

        user = self.getCurrentUser()

        image = self.model('image', 'isic_archive').load(
            body_json['imageId'], level=AccessType.READ, user=user)

        lesionBoundary = body_json['lesionBoundary']
        lesionBoundary['properties']['startTime'] = datetime.datetime.utcfromtimestamp(
            lesionBoundary['properties']['startTime'] / 1000.0)
        lesionBoundary['properties']['stopTime'] = datetime.datetime.utcfromtimestamp(
            lesionBoundary['properties']['stopTime'] / 1000.0)

        skill = Segmentation.getUserSkill(user)
        if skill is None:
            raise RestException('Current user is not authorized to create segmentations.')

        segmentation = Segmentation.createSegmentation(
            image=image,
            skill=skill,
            creator=user,
            lesionBoundary=lesionBoundary
        )

        # Move image item to next collection
        if skill == Segmentation.Skill.EXPERT:
            next_phase_collection = ISIC.LesionImages.collection
        else:
            next_phase_collection = ISIC.Phase1b.collection
        original_folder = Folder.load(image['folderId'], force=True)
        next_phase_folder = Folder.createFolder(
            parent=next_phase_collection,
            name=original_folder['name'],
            description=original_folder['description'],
            parentType='collection',
            public=None,
            creator=getAdminUser(),
            allowRename=False,
            reuseExisting=True
        )
        if not next_phase_folder.get('meta'):
            next_phase_folder = Folder.setMetadata(
                next_phase_folder, original_folder['meta'])

        self.model('item').move(image, next_phase_folder)

        return segmentation


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

        return segmentation


    @describeRoute(
        Description('Get a thumbnail, showing a segmentation.')
        .param('id', 'The ID of the segmentation.', paramType='path')
        .param('width', 'The desired width for the thumbnail.',
               paramType='query', required=False, default=256)
        .param('contentDisposition', 'Specify the Content-Disposition response '
               'header disposition-type value', required=False,
               enum=['inline', 'attachment'])
        .errorResponse('ID was invalid.')
    )
    @access.cookie
    @access.public
    @rawResponse
    @loadmodel(model='segmentation', plugin='isic_archive')
    def thumbnail(self, segmentation, params):
        contentDisp = params.get('contentDisposition', None)
        if contentDisp is not None and \
                contentDisp not in {'inline', 'attachment'}:
            raise RestException('Unallowed contentDisposition type "%s".' %
                                contentDisp)

        # TODO: convert this to make Segmentation use an AccessControlMixin
        image = self.model('image', 'isic_archive').load(
            segmentation['imageId'], level=AccessType.READ,
            user=self.getCurrentUser(), exc=True)

        width = int(params.get('width', 256))

        thumbnail_image_stream = self.model('segmentation', 'isic_archive').boundaryThumbnail(
            segmentation, image, width)
        thumbnail_image_data = thumbnail_image_stream.getvalue()

        cherrypy.response.headers['Content-Type'] = 'image/jpeg'
        content_name = '%s_segmentation_thumbnail.jpg' % image['_id']
        if contentDisp == 'inline':
            cherrypy.response.headers['Content-Disposition'] = \
                'inline; filename="%s"' % content_name
        else:
            cherrypy.response.headers['Content-Disposition'] = \
                'attachment; filename="%s"' % content_name
        cherrypy.response.headers['Content-Length'] = len(thumbnail_image_data)

        return thumbnail_image_data


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
