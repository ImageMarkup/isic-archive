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

import base64
import datetime

import numpy
import six

from girder.api import access
from girder.api.rest import loadmodel, setRawResponse, setResponseHeader
from girder.api.describe import Description, describeRoute
from girder.constants import AccessType, SortDir
from girder.exceptions import RestException, ValidationException
from girder.models.file import File

from .base import IsicResource
from ..models.image import Image
from ..models.segmentation import Segmentation
from ..models.segmentation_helpers import OpenCVSegmentationHelper, ScikitSegmentationHelper
from ..models.user import User


class SegmentationResource(IsicResource):
    def __init__(self,):
        super(SegmentationResource, self).__init__()
        self.resourceName = 'segmentation'

        self.route('GET', (), self.find)
        self.route('POST', (), self.createSegmentation)
        self.route('GET', (':id',), self.getSegmentation)
        self.route('GET', (':id', 'mask'), self.mask)
        self.route('GET', (':id', 'thumbnail'), self.thumbnail)
        self.route('POST', (':id', 'review'), self.doReview)

    @describeRoute(
        Description('List the segmentations for an image.')
        .pagingParams(defaultSort='created', defaultSortDir=-1)
        .param('imageId', 'The ID of the image.')
        .param('creatorId', 'The ID of the creator user.', required=False)
        .errorResponse('ID was invalid.')
    )
    @access.cookie
    @access.public
    def find(self, params):
        self.requireParams(['imageId'], params)
        limit, offset, sort = self.getPagingParameters(
            params, defaultSortField='created', defaultSortDir=SortDir.DESCENDING)

        image = Image().load(
            params['imageId'], level=AccessType.READ, user=self.getCurrentUser(), exc=True)

        filters = {
            'imageId': image['_id']
        }
        if 'creatorId' in params:
            # Ensure that the user exists
            creatorUser = User().load(params['creatorId'], force=True, exc=True)
            filters['creatorId'] = creatorUser['_id']

        return [
            {
                '_id': segmentation['_id'],
                'created': segmentation['created'],
                'failed': segmentation['maskId'] is None,
                'skill':
                    'expert'
                    if any(
                        review['skill'] == Segmentation().Skill.EXPERT
                        for review in segmentation['reviews']
                    )
                    else 'novice'
            }
            for segmentation in Segmentation().find(
                query=filters,
                sort=sort,
                limit=limit,
                offset=offset,
            )
        ]

    @describeRoute(
        Description('Add a segmentation to an image.')
        .param('imageId', 'The ID of the image.', paramType='body')
        .param('mask', 'A Base64-encoded PNG 8-bit image, containing the segmentation mask.',
               paramType='body')
        .param('failed', 'Whether the segmentation should be marked as a failure.',
               paramType='body', dataType='boolean', required=False)
        .errorResponse('ID was invalid.')
    )
    @access.user
    def createSegmentation(self, params):
        params = self._decodeParams(params)
        self.requireParams(['imageId'], params)

        user = self.getCurrentUser()
        User().requireSegmentationSkill(user)

        image = Image().load(params['imageId'], level=AccessType.READ, user=user, exc=True)

        failed = self.boolParam('failed', params)

        if failed:
            segmentation = Segmentation().createSegmentation(
                image=image,
                creator=user,
                mask=None,
                meta={
                    'flagged': 'could not segment'
                }
            )
        elif 'lesionBoundary' in params:
            lesionBoundary = params['lesionBoundary']

            meta = lesionBoundary['properties']
            meta['startTime'] = datetime.datetime.utcfromtimestamp(meta['startTime'] / 1000.0),
            meta['stopTime'] = datetime.datetime.utcfromtimestamp(meta['stopTime'] / 1000.0)

            if meta.get('source') == 'autofill':
                # Since converting an autofill coordinate list back to a mask
                # sometimes crates disconnected mask components, just redo the
                # autofill segmentation internally.
                # Note, this code will all go away once masks are used directly
                # by the client.
                seedCoord = meta['seedPoint']
                if not (
                    isinstance(seedCoord, list) and
                    len(seedCoord) == 2 and
                    all(isinstance(value, int) for value in seedCoord)
                ):
                    raise ValidationException('Value must be a coordinate pair.', 'seedPoint')

                tolerance = meta['tolerance']
                if not isinstance(tolerance, int):
                    raise ValidationException('Value must be an integer.', 'tolerance')

                mask = Segmentation().doSegmentation(image, seedCoord, tolerance)
            else:
                coords = lesionBoundary['geometry']['coordinates'][0]
                mask = OpenCVSegmentationHelper.contourToMask(
                    (
                        image['meta']['acquisition']['pixelsY'],
                        image['meta']['acquisition']['pixelsX']
                    ),
                    numpy.rint(numpy.array(coords)).astype(int)
                )

            segmentation = Segmentation().createSegmentation(
                image=image,
                creator=user,
                mask=mask,
                meta=meta
            )
        elif 'mask' in params:
            maskStream = six.BytesIO()
            maskStream.write(base64.b64decode(params['mask']))
            mask = ScikitSegmentationHelper.loadImage(maskStream)

            segmentation = Segmentation().createSegmentation(
                image=image,
                creator=user,
                mask=mask,
                meta={}
            )
        else:
            raise RestException('One of "failed", "lesionBoundary", or "mask" must be present')

        # TODO: return 201?
        # TODO: remove maskId from return?
        return segmentation

    @describeRoute(
        Description('Get a segmentation for an image.')
        .param('id', 'The ID of the segmentation.', paramType='path')
        .errorResponse('ID was invalid.')
    )
    @access.cookie
    @access.public
    @loadmodel(model='segmentation', plugin='isic_archive')
    def getSegmentation(self, segmentation, params):
        # TODO: convert this to make Segmentation use an AccessControlMixin
        Image().load(
            segmentation['imageId'], level=AccessType.READ, user=self.getCurrentUser(), exc=True)

        segmentation['creator'] = User().filterSummary(
            User().load(segmentation.pop('creatorId'), force=True, exc=True),
            self.getCurrentUser())

        segmentation['failed'] = segmentation.pop('maskId') is None

        return segmentation

    @describeRoute(
        Description('Get a segmentation, rendered as a binary mask.')
        .param('id', 'The ID of the segmentation.', paramType='path')
        .param('contentDisposition',
               'Specify the Content-Disposition response header disposition-type value.',
               required=False, enum=['inline', 'attachment'])
        .produces('image/png')
        .errorResponse('ID was invalid.')
    )
    @access.cookie
    @access.public
    @loadmodel(model='segmentation', plugin='isic_archive')
    def mask(self, segmentation, params):
        contentDisp = params.get('contentDisposition', None)
        if contentDisp is not None and contentDisp not in {'inline', 'attachment'}:
            raise ValidationException('Unallowed contentDisposition type "%s".' % contentDisp,
                                      'contentDisposition')

        # TODO: convert this to make Segmentation use an AccessControlMixin
        Image().load(
            segmentation['imageId'], level=AccessType.READ, user=self.getCurrentUser(), exc=True)

        maskFile = Segmentation().maskFile(segmentation)
        if maskFile is None:
            raise RestException('This segmentation is failed, and thus has no mask.', code=410)

        return File().download(maskFile, headers=True, contentDisposition=contentDisp)

    @describeRoute(
        Description('Get a segmentation, rendered as a thumbnail with a boundary overlay.')
        .param('id', 'The ID of the segmentation.', paramType='path')
        .param('width', 'The desired width for the thumbnail.', paramType='query', required=False,
               default=256)
        .param('contentDisposition',
               'Specify the Content-Disposition response header disposition-type value.',
               required=False, enum=['inline', 'attachment'])
        .produces('image/jpeg')
        .errorResponse('ID was invalid.')
    )
    @access.cookie
    @access.public
    @loadmodel(model='segmentation', plugin='isic_archive')
    def thumbnail(self, segmentation, params):
        contentDisp = params.get('contentDisposition', None)
        if contentDisp is not None and contentDisp not in {'inline', 'attachment'}:
            raise ValidationException('Unallowed contentDisposition type "%s".' % contentDisp,
                                      'contentDisposition')

        # TODO: convert this to make Segmentation use an AccessControlMixin
        image = Image().load(
            segmentation['imageId'], level=AccessType.READ, user=self.getCurrentUser(), exc=True)

        width = int(params.get('width', 256))

        thumbnailImageStream = Segmentation().boundaryThumbnail(segmentation, image, width)
        if thumbnailImageStream is None:
            raise RestException('This segmentation is failed, and thus has no thumbnail.', code=410)
        thumbnailImageData = thumbnailImageStream.getvalue()

        # Only setRawResponse now, as this handler may return a JSON error
        # earlier
        setRawResponse()
        setResponseHeader('Content-Type', 'image/jpeg')
        contentName = '%s_segmentation_thumbnail.jpg' % image['name']
        if contentDisp == 'inline':
            setResponseHeader('Content-Disposition', 'inline; filename="%s"' % contentName)
        else:
            setResponseHeader('Content-Disposition', 'attachment; filename="%s"' % contentName)
        setResponseHeader('Content-Length', len(thumbnailImageData))

        return thumbnailImageData

    @describeRoute(
        Description('Review a segmentation.')
        .param('id', 'The ID of the segmentation.', paramType='path')
        .param('approved', 'Whether the segmentation was approved by the user.', paramType='body',
               dataType='boolean')
        .errorResponse('ID was invalid.')
    )
    @access.user
    @loadmodel(model='segmentation', plugin='isic_archive')
    def doReview(self, segmentation, params):
        params = self._decodeParams(params)
        self.requireParams(['approved'], params)

        approved = self.boolParam('approved', params)

        user = self.getCurrentUser()
        User().requireSegmentationSkill(user)

        segmentation = Segmentation().review(segmentation, approved, user)

        # TODO: return 201?
        # TODO: remove maskId from return?
        return segmentation
