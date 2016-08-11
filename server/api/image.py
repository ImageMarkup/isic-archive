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

import cherrypy

from girder.api import access
from girder.api.rest import Resource, RestException, loadmodel
from girder.api.describe import Description, describeRoute
from girder.constants import AccessType
from girder.models.model_base import GirderException


class ImageResource(Resource):
    def __init__(self,):
        super(ImageResource, self).__init__()
        self.resourceName = 'image'

        self.route('GET', (), self.find)
        self.route('GET', (':id',), self.getImage)
        self.route('GET', (':id', 'thumbnail'), self.thumbnail)
        self.route('GET', (':id', 'download'), self.download)

        self.route('POST', (':id', 'flag'), self.flag)
        self.route('POST', (':id', 'segment'), self.doSegmentation)

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
        output = self.model('image', 'isic_archive').filter(
            image, self.getCurrentUser())

        if 'originalFilename' in output['meta']:
            currentUser = self.getCurrentUser()
            if not (currentUser and currentUser['admin']):
                del output['meta']['originalFilename']

        return output

    @describeRoute(
        Description('Return an image\'s thumbnail.')
        .param('id', 'The ID of the image.', paramType='path')
        .param('width', 'The desired width for the thumbnail.',
               paramType='query', required=False, default=256)
        .errorResponse('ID was invalid.')
    )
    @access.cookie
    @access.public
    @loadmodel(model='image', plugin='isic_archive', level=AccessType.READ)
    def thumbnail(self, image, params):
        width = int(params.get('width', 256))

        thumbData, thumbMime = self.model('image_item', 'large_image')\
            .getThumbnail(image, width=width)

        cherrypy.response.headers['Content-Type'] = thumbMime
        return lambda: thumbData

    @describeRoute(
        Description('Download an image\'s high-quality original binary data.')
        .param('id', 'The ID of the image.', paramType='path')
        .param('contentDisposition', 'Specify the Content-Disposition response '
               'header disposition-type value', required=False,
               enum=['inline', 'attachment'])
        .errorResponse('ID was invalid.')
    )
    @access.cookie
    @access.public
    @loadmodel(model='image', plugin='isic_archive', level=AccessType.READ)
    def download(self, image, params):
        contentDisp = params.get('contentDisposition', None)
        if contentDisp is not None and \
                contentDisp not in {'inline', 'attachment'}:
            raise RestException('Unallowed contentDisposition type "%s".' %
                                contentDisp)

        original_file = self.model('image', 'isic_archive').originalFile(image)
        file_stream = self.model('file').download(original_file, headers=True)

        # TODO: replace this after https://github.com/girder/girder/pull/1123
        if contentDisp == 'inline':
            cherrypy.response.headers['Content-Disposition'] = \
                'inline; filename="%s"' % original_file['name']
        return file_stream

    @describeRoute(
        Description('Flag an image with a problem.')
        .param('id', 'The ID of the image.', paramType='path')
        .errorResponse('ID was invalid.')
    )
    @access.user
    @loadmodel(model='image', plugin='isic_archive', level=AccessType.READ)
    def flag(self, image, params):
        bodyJson = self.getBodyJson()
        self.requireParams(('reason',), bodyJson)

        self.model('image', 'isic_archive').flag(
            image, bodyJson['reason'], self.getCurrentUser())

        return {'status': 'success'}

    @describeRoute(
        Description('Run and return a new semi-automated segmentation.')
        .param('id', 'The ID of the image.', paramType='path')
        .param('seed', 'The X, Y coordinates of a segmentation seed point.',
               paramType='body')
        .param('tolerance',
               'The intensity tolerance value for the segmentation.',
               paramType='body')
        .errorResponse('ID was invalid.')
    )
    @access.user
    @loadmodel(model='image', plugin='isic_archive', level=AccessType.READ)
    def doSegmentation(self, image, params):
        bodyJson = self.getBodyJson()
        self.requireParams(('seed', 'tolerance'), bodyJson)

        # validate parameters
        seedCoord = bodyJson['seed']
        if not (
            isinstance(seedCoord, list) and
            len(seedCoord) == 2 and
            all(isinstance(value, int) for value in seedCoord)
        ):
            raise RestException('Submitted "seed" must be a coordinate pair.')

        tolerance = bodyJson['tolerance']
        if not isinstance(tolerance, int):
            raise RestException('Submitted "tolerance" must be an integer.')

        try:
            contourFeature = self.model('image', 'isic_archive').doSegmentation(
                image, seedCoord, tolerance)
        except GirderException as e:
            raise RestException(e.message)

        return contourFeature
