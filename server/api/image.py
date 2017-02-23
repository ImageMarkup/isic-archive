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

import json

from bson import ObjectId
from bson.errors import InvalidId
import geojson

from girder.api import access
from girder.api.rest import Resource, RestException, loadmodel, rawResponse, \
    setResponseHeader
from girder.api.describe import Description, describeRoute
from girder.constants import AccessType
from girder.models.model_base import GirderException

from ..utility import querylang


class ImageResource(Resource):
    def __init__(self,):
        super(ImageResource, self).__init__()
        self.resourceName = 'image'

        self.route('GET', (), self.find)
        self.route('GET', ('histogram',), self.getHistogram)
        self.route('GET', (':id',), self.getImage)
        self.route('GET', (':id', 'thumbnail'), self.thumbnail)
        self.route('GET', (':id', 'download'), self.download)
        self.route('GET', (':id', 'superpixels'), self.getSuperpixels)

        self.route('POST', (':id', 'segment'), self.doSegmentation)

    @describeRoute(
        Description('Return a list of lesion images.')
        .pagingParams(defaultSort='name')
        .param('datasetId', 'The ID of the dataset to use.', required=False)
        .param('name', 'Find an image with a specific name.',
               required=False)
        .param('filter', 'Filter the images by a PegJS-specified grammar '
                         '(causing "datasetId" and "name" to be ignored).',
               required=False)
        .errorResponse()
    )
    @access.public
    def find(self, params):
        Image = self.model('image', 'isic_archive')

        user = self.getCurrentUser()
        limit, offset, sort = self.getPagingParameters(params, 'name')

        if 'filter' in params:
            query = querylang.astToMongo(json.loads(params['filter']))
        else:
            query = {}
            if 'datasetId' in params:
                try:
                    query.update({'folderId': ObjectId(params['datasetId'])})
                except InvalidId:
                    raise RestException(
                        'Invalid "folderId" ObjectId: %s' % params['datasetId'])
            if 'name' in params:
                query.update({'name': params['name']})

        return [
            {
                field: image[field]
                for field in
                Image.summaryFields
            }
            for image in
            Image.filterResultsByPermission(
                # TODO: exclude additional fields from the cursor
                Image.find(query, sort=sort, fields={'meta': 0}),
                user=user, level=AccessType.READ, limit=limit, offset=offset)
        ]

    @describeRoute(
        Description('Return histograms of image metadata.')
        .param('filter',
               'Get the histogram after the results of this filter. ' +
               'TODO: describe our filter grammar (an AST tree).',
               required=False)
        .errorResponse()
    )
    @access.public
    def getHistogram(self, params):
        Image = self.model('image', 'isic_archive')

        filters = params.get('filter')
        if filters is not None:
            filters = json.loads(filters)
        user = self.getCurrentUser()
        return Image.getHistograms(filters, user)

    @describeRoute(
        Description('Return an image\'s details.')
        .param('id', 'The ID of the image.', paramType='path')
        .errorResponse('ID was invalid.')
    )
    @access.public
    @loadmodel(model='image', plugin='isic_archive', level=AccessType.READ)
    def getImage(self, image, params):
        Dataset = self.model('dataset', 'isic_archive')
        Image = self.model('image', 'isic_archive')
        User = self.model('user', 'isic_archive')

        user = self.getCurrentUser()

        output = Image.filter(image, user)
        output['_modelType'] = 'image'

        output['dataset'] = Dataset.load(
            output.pop('folderId'),
            force=True, exc=True,
            # Work around a bug in upstream Girder
            fields=Dataset.summaryFields + ['baseParentType', 'lowerName']
        )
        del output['dataset']['baseParentType']
        del output['dataset']['lowerName']

        output['creator'] = User.filteredSummary(
            User.load(
                output.pop('creatorId'),
                force=True, exc=True),
            user)

        if User.canReviewDataset(user):
            output['privateMeta'] = image['privateMeta']

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
    @rawResponse
    @loadmodel(model='image', plugin='isic_archive', level=AccessType.READ)
    def thumbnail(self, image, params):
        width = int(params.get('width', 256))

        thumbData, thumbMime = self.model('image_item', 'large_image')\
            .getThumbnail(image, width=width)

        setResponseHeader('Content-Type', thumbMime)
        return thumbData

    @describeRoute(
        Description('Download an image\'s high-quality original binary data.')
        .param('id', 'The ID of the image.', paramType='path')
        .param('contentDisposition', 'Specify the Content-Disposition response '
               'header disposition-type value.', required=False,
               enum=['inline', 'attachment'])
        .errorResponse('ID was invalid.')
    )
    @access.cookie
    @access.public
    @loadmodel(model='image', plugin='isic_archive', level=AccessType.READ)
    def download(self, image, params):
        File = self.model('file')
        Image = self.model('image', 'isic_archive')

        contentDisp = params.get('contentDisposition', None)
        if contentDisp is not None and \
                contentDisp not in {'inline', 'attachment'}:
            raise RestException('Unallowed contentDisposition type "%s".' %
                                contentDisp)

        originalFile = Image.originalFile(image)
        fileStream = File.download(
            originalFile, headers=True, contentDisposition=contentDisp)
        return fileStream

    @describeRoute(
        Description('Get the superpixels for this image, as a PNG-encoded '
                    'label map.')
        .param('id', 'The ID of the image.', paramType='path')
        .errorResponse('ID was invalid.')
    )
    @access.cookie
    @access.public
    @loadmodel(model='image', plugin='isic_archive', level=AccessType.READ)
    def getSuperpixels(self, image, params):
        File = self.model('file')
        Image = self.model('image', 'isic_archive')

        superpixelsFile = Image.superpixelsFile(image)
        return File.download(superpixelsFile, headers=True)

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
        Segmentation = self.model('segmentation', 'isic_archive')
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
            contourCoords = Segmentation.doContourSegmentation(
                image, seedCoord, tolerance)
        except GirderException as e:
            raise RestException(e.message)

        contourFeature = geojson.Feature(
            geometry=geojson.Polygon(
                coordinates=(contourCoords.tolist(),)
            ),
            properties={
                'source': 'autofill',
                'seedPoint': seedCoord,
                'tolerance': tolerance
            }
        )

        return contourFeature
