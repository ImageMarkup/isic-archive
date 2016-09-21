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

from girder.api import access
from girder.api.rest import Resource, RestException, loadmodel, rawResponse, \
    setResponseHeader
from girder.api.describe import Description, describeRoute
from girder.constants import AccessType, SortDir


class SegmentationResource(Resource):
    def __init__(self,):
        super(SegmentationResource, self).__init__()
        self.resourceName = 'segmentation'

        self.route('GET', (), self.find)
        self.route('POST', (), self.createSegmentation)
        self.route('GET', (':id',), self.getSegmentation)
        self.route('GET', (':id', 'mask'), self.mask)
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
        User = self.model('user', 'isic_archive')

        bodyJson = self.getBodyJson()
        self.requireParams(('imageId', 'lesionBoundary'), bodyJson)

        user = self.getCurrentUser()

        image = self.model('image', 'isic_archive').load(
            bodyJson['imageId'], level=AccessType.READ, user=user, exc=True)

        lesionBoundary = bodyJson['lesionBoundary']
        lesionBoundary['properties']['startTime'] = \
            datetime.datetime.utcfromtimestamp(
                lesionBoundary['properties']['startTime'] / 1000.0)
        lesionBoundary['properties']['stopTime'] = \
            datetime.datetime.utcfromtimestamp(
                lesionBoundary['properties']['stopTime'] / 1000.0)

        skill = User.requireSegmentationSkill(user)

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
        Image = self.model('image', 'isic_archive')
        User = self.model('user', 'isic_archive')

        # TODO: convert this to make Segmentation use an AccessControlMixin
        Image.load(
            segmentation['imageId'], level=AccessType.READ,
            user=self.getCurrentUser(), exc=True)

        segmentation['creator'] = User.filteredSummary(
            User.load(
                segmentation.pop('creatorId'),
                force=True, exc=True),
            self.getCurrentUser())

        return segmentation

    @describeRoute(
        Description('Get a segmentation, rendered as a binary mask.')
        .param('id', 'The ID of the segmentation.', paramType='path')
        .param('contentDisposition', 'Specify the Content-Disposition response '
               'header disposition-type value.', required=False,
               enum=['inline', 'attachment'])
        .errorResponse('ID was invalid.')
    )
    @access.cookie
    @access.public
    @rawResponse
    @loadmodel(model='segmentation', plugin='isic_archive')
    def mask(self, segmentation, params):
        Image = self.model('image', 'isic_archive')
        Segmentation = self.model('segmentation', 'isic_archive')
        contentDisp = params.get('contentDisposition', None)
        if contentDisp is not None and \
                contentDisp not in {'inline', 'attachment'}:
            raise RestException('Unallowed contentDisposition type "%s".' %
                                contentDisp)

        # TODO: convert this to make Segmentation use an AccessControlMixin
        image = Image.load(
            segmentation['imageId'], level=AccessType.READ,
            user=self.getCurrentUser(), exc=True)

        renderedMaskStream = Segmentation.renderedMask(segmentation, image)
        renderedMaskData = renderedMaskStream.getvalue()

        setResponseHeader('Content-Type', 'image/png')
        contentName = '%s_segmentation_mask.png' % image['_id']
        if contentDisp == 'inline':
            setResponseHeader(
                'Content-Disposition',
                'inline; filename="%s"' % contentName)
        else:
            setResponseHeader(
                'Content-Disposition',
                'attachment; filename="%s"' % contentName)
        setResponseHeader('Content-Length', len(renderedMaskData))

        return renderedMaskData

    @describeRoute(
        Description('Get a segmentation, rendered as a thumbnail with a '
                    'boundary overlay.')
        .param('id', 'The ID of the segmentation.', paramType='path')
        .param('width', 'The desired width for the thumbnail.',
               paramType='query', required=False, default=256)
        .param('contentDisposition', 'Specify the Content-Disposition response '
               'header disposition-type value.', required=False,
               enum=['inline', 'attachment'])
        .errorResponse('ID was invalid.')
    )
    @access.cookie
    @access.public
    @rawResponse
    @loadmodel(model='segmentation', plugin='isic_archive')
    def thumbnail(self, segmentation, params):
        Image = self.model('image', 'isic_archive')
        Segmentation = self.model('segmentation', 'isic_archive')
        contentDisp = params.get('contentDisposition', None)
        if contentDisp is not None and \
                contentDisp not in {'inline', 'attachment'}:
            raise RestException('Unallowed contentDisposition type "%s".' %
                                contentDisp)

        # TODO: convert this to make Segmentation use an AccessControlMixin
        image = Image.load(
            segmentation['imageId'], level=AccessType.READ,
            user=self.getCurrentUser(), exc=True)

        width = int(params.get('width', 256))

        thumbnailImageStream = Segmentation.boundaryThumbnail(
            segmentation, image, width)
        thumbnailImageData = thumbnailImageStream.getvalue()

        setResponseHeader('Content-Type', 'image/jpeg')
        contentName = '%s_segmentation_thumbnail.jpg' % image['_id']
        if contentDisp == 'inline':
            setResponseHeader(
                'Content-Disposition',
                'inline; filename="%s"' % contentName)
        else:
            setResponseHeader(
                'Content-Disposition',
                'attachment; filename="%s"' % contentName)
        setResponseHeader('Content-Length', len(thumbnailImageData))

        return thumbnailImageData
