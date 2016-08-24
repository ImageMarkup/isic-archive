#!/usr/bin/env python
# -*- coding: utf-8 -*-

###############################################################################
#  Copyright Kitware Inc.
#
#  Licensed under the Apache License, Version 2.0 ( the "License" );
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
###############################################################################

import datetime

import cherrypy

from girder.api import access
from girder.api.rest import Resource, RestException, loadmodel, rawResponse
from girder.api.describe import Description, describeRoute
from girder.constants import AccessType, SortDir


class SegmentationResource(Resource):
    def __init__(self,):
        super(SegmentationResource, self).__init__()
        self.resourceName = 'segmentation'

        self.route('GET', (), self.find)
        self.route('POST', (), self.createSegmentation)
        self.route('GET', (':id',), self.getSegmentation)
        self.route('GET', (':id', 'thumbnail'), self.thumbnail)

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

        bodyJson = self.getBodyJson()
        self.requireParams(('imageId', 'lesionBoundary'), bodyJson)

        user = self.getCurrentUser()

        image = self.model('image', 'isic_archive').load(
            bodyJson['imageId'], level=AccessType.READ, user=user)

        lesionBoundary = bodyJson['lesionBoundary']
        lesionBoundary['properties']['startTime'] = \
            datetime.datetime.utcfromtimestamp(
                lesionBoundary['properties']['startTime'] / 1000.0)
        lesionBoundary['properties']['stopTime'] = \
            datetime.datetime.utcfromtimestamp(
                lesionBoundary['properties']['stopTime'] / 1000.0)

        skill = Segmentation.getUserSkill(user)
        if skill is None:
            raise RestException(
                'Current user is not authorized to create segmentations.')

        segmentation = Segmentation.createSegmentation(
            image=image,
            skill=skill,
            creator=user,
            lesionBoundary=lesionBoundary
        )
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
        Segmentation = self.model('segmentation', 'isic_archive')
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

        thumbnailImageStream = Segmentation.boundaryThumbnail(
            segmentation, image, width)
        thumbnailImageData = thumbnailImageStream.getvalue()

        cherrypy.response.headers['Content-Type'] = 'image/jpeg'
        contentName = '%s_segmentation_thumbnail.jpg' % image['_id']
        if contentDisp == 'inline':
            cherrypy.response.headers['Content-Disposition'] = \
                'inline; filename="%s"' % contentName
        else:
            cherrypy.response.headers['Content-Disposition'] = \
                'attachment; filename="%s"' % contentName
        cherrypy.response.headers['Content-Length'] = len(thumbnailImageData)

        return thumbnailImageData
