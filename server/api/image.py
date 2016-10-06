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

from girder.api import access
from girder.api.rest import Resource, RestException, loadmodel, rawResponse, \
    setResponseHeader
from girder.api.describe import Description, describeRoute
from girder.constants import AccessType
from girder.models.model_base import GirderException

from ..histogram_utility import HistogramUtility
from ..histogram_utility import querylang


class ImageResource(Resource):
    def __init__(self,):
        super(ImageResource, self).__init__()
        self.resourceName = 'image'

        self.route('GET', (), self.find)
        self.route('GET', (':id',), self.getImage)
        self.route('GET', (':id', 'thumbnail'), self.thumbnail)
        self.route('GET', (':id', 'download'), self.download)
        self.route('GET', (':id', 'superpixels'), self.getSuperpixels)

        self.route('GET', ('histogram',), self.histogram)
        self.histogramUtility = HistogramUtility()

        self.route('POST', (':id', 'segment'), self.doSegmentation)

    @describeRoute(
        Description('Return a list of lesion images.')
        .pagingParams(defaultSort='lowerName')
        .param('datasetId', 'The ID of the dataset to use.', required=False)
        .param('filter', 'Filter the images by a PegJS-specified grammar '
                         '(causing "datasetId" to be ignored).',
               required=False)
        .errorResponse()
    )
    @access.public
    def find(self, params):
        Image = self.model('image', 'isic_archive')

        user = self.getCurrentUser()
        limit, offset, sort = self.getPagingParameters(params, 'lowerName')

        if 'filter' in params:
            query = querylang.astToMongo(json.loads(params['filter']))
        elif 'datasetId' in params:
            # ensure the user has access to the dataset
            try:
                query = {'folderId': params['datasetId']}
            except:
                raise RestException(
                    'Invalid "folderId" ObjectId: %s' % params['datasetId'])
        else:
            query = {}

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

        output = Image.filter(image, self.getCurrentUser())
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
            self.getCurrentUser())

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
        contentDisp = params.get('contentDisposition', None)
        if contentDisp is not None and \
                contentDisp not in {'inline', 'attachment'}:
            raise RestException('Unallowed contentDisposition type "%s".' %
                                contentDisp)

        originalFile = self.model('image', 'isic_archive').originalFile(image)
        fileStream = self.model('file').download(
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
        superpixelsFile = self.model('image', 'isic_archive').superpixelsFile(
            image)
        return self.model('file').download(superpixelsFile, headers=True)

    @describeRoute(
        Description('Return histograms of image metadata.')
        .param('filter',
               'Get the histogram after the results of this filter. ' +
               'TODO: describe our filter grammar (an AST tree).',
               required=False)
        .param('limit', 'Result set size limit. Setting to 0 will create ' +
               'a histogram using all the matching items (default=0).',
               required=False, dataType='int')
        .param('offset', 'Offset into result set (default=0).',
               required=False, dataType='int')
        .errorResponse()
    )
    @access.public
    def histogram(self, params):
        user = self.getCurrentUser()

        return self.histogramUtility.getHistograms(user, params)

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
            contourFeature = Segmentation.doSegmentation(
                image, seedCoord, tolerance)
        except GirderException as e:
            raise RestException(e.message)

        return contourFeature
