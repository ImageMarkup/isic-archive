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

import os
import json

from bson import ObjectId
from bson.errors import InvalidId
import geojson
import six

from girder.api import access
from girder.api.rest import RestException, loadmodel, setRawResponse, setResponseHeader
from girder.api.describe import Description, describeRoute
from girder.constants import AccessType
from girder.models.model_base import GirderException, ValidationException
from girder.utility import mail_utils, ziputil
from girder.plugins.large_image.models import TileGeneralException

from .base import IsicResource
from ..utility import querylang


class ImageResource(IsicResource):
    def __init__(self,):
        super(ImageResource, self).__init__()
        self.resourceName = 'image'

        self.route('GET', (), self.find)
        self.route('GET', ('download',), self.downloadMultiple)
        self.route('GET', ('histogram',), self.getHistogram)
        self.route('GET', (':id',), self.getImage)
        self.route('GET', (':id', 'thumbnail'), self.thumbnail)
        self.route('GET', (':id', 'tiles'), self.getTileInfo)
        self.route('GET', (':id', 'tiles', ':z', ':x', ':y'), self.getTile)
        self.route('GET', (':id', 'download'), self.download)
        self.route('GET', (':id', 'superpixels'), self.getSuperpixels)

        self.route('POST', (':id', 'segment'), self.doSegmentation)

    def _parseFilter(self, filterParam):
        if isinstance(filterParam, six.string_types):
            try:
                filterParam = json.loads(filterParam)
            except ValueError as e:
                raise ValidationException('Could not decode JSON: %s' % str(e), 'filter')
        try:
            return querylang.astToMongo(filterParam)
        except (TypeError, ValueError) as e:
            raise ValidationException('Could not parse filter:' % str(e), 'filter')

    @describeRoute(
        Description('Return a list of lesion images.')
        .pagingParams(defaultSort='name')
        .param('datasetId', 'The ID of the dataset to use.', required=False)
        .param('name', 'Find an image with a specific name.', required=False)
        .param('filter', 'Filter the images by a PegJS-specified grammar (causing "datasetId" and '
                         '"name" to be ignored).',
               required=False)
        .errorResponse()
    )
    @access.cookie
    @access.public
    def find(self, params):
        Image = self.model('image', 'isic_archive')

        user = self.getCurrentUser()
        limit, offset, sort = self.getPagingParameters(params, 'name')

        if 'filter' in params:
            query = self._parseFilter(params['filter'])
        else:
            query = {}
            if 'datasetId' in params:
                try:
                    query.update({'folderId': ObjectId(params['datasetId'])})
                except InvalidId:
                    raise ValidationException('Invalid ObjectId.', 'datasetId')
            if 'name' in params:
                query.update({'name': params['name']})

        return [
            Image.filterSummary(image, user)
            for image in
            Image.filterResultsByPermission(
                # TODO: exclude additional fields from the cursor
                Image.find(query, sort=sort, fields={'meta': 0}),
                user=user, level=AccessType.READ, limit=limit, offset=offset)
        ]

    @describeRoute(
        Description('Download multiple images as a ZIP file.')
        .param('datasetId', 'The ID of the dataset to download.', required=False)
        .param('filter', 'Filter the images by a PegJS-specified grammar (causing "datasetId" to '
                         'be ignored).',
               required=False)
        .errorResponse()
    )
    @access.cookie
    @access.public
    def downloadMultiple(self, params):
        Dataset = self.model('dataset', 'isic_archive')
        File = self.model('file')
        Image = self.model('image', 'isic_archive')

        if 'filter' in params:
            query = self._parseFilter(params['filter'])
        else:
            query = {}
            if 'datasetId' in params:
                try:
                    query.update({'folderId': ObjectId(params['datasetId'])})
                except InvalidId:
                    raise ValidationException('Invalid ObjectId.', 'datasetId')

        user = self.getCurrentUser()
        downloadFileName = 'ISIC-images'

        def stream():
            datasetCache = {}
            zipGenerator = ziputil.ZipGenerator(downloadFileName)

            for image in Image.filterResultsByPermission(
                    # TODO: exclude additional fields from the cursor
                    Image.find(query, sort=[('name', 1)], fields={'meta': 0}),
                    user=user, level=AccessType.READ, limit=0, offset=0):
                datasetId = image['folderId']
                if datasetId not in datasetCache:
                    datasetCache[datasetId] = Dataset.load(datasetId, force=True, exc=True)
                dataset = datasetCache[datasetId]
                imageFile = Image.originalFile(image)
                imageFileGenerator = File.download(imageFile, headers=False)
                for data in zipGenerator.addFile(
                        imageFileGenerator,
                        path=os.path.join(dataset['name'], imageFile['name'])):
                    yield data

            for dataset in six.viewvalues(datasetCache):
                licenseText = mail_utils.renderTemplate(
                    'license_%s.mako' % dataset['meta']['license'])
                attributionText = mail_utils.renderTemplate(
                    'attribution_%s.mako' % dataset['meta']['license'],
                    {
                        'work': dataset['name'],
                        'author':
                            dataset['meta']['attribution']
                            if not dataset['meta']['anonymous']
                            else 'Anonymous'
                    })
                for data in zipGenerator.addFile(
                        lambda: [licenseText],
                        path=os.path.join(dataset['name'], 'LICENSE.txt')):
                    yield data
                for data in zipGenerator.addFile(
                        lambda: [attributionText],
                        path=os.path.join(dataset['name'], 'ATTRIBUTION.txt')):
                    yield data

            yield zipGenerator.footer()

        setResponseHeader('Content-Type', 'application/zip')
        setResponseHeader('Content-Disposition', 'attachment; filename="%s.zip"' % downloadFileName)
        return stream

    @describeRoute(
        Description('Return histograms of image metadata.')
        .param('filter', 'Filter the images by a PegJS-specified grammar.', required=False)
        .errorResponse()
    )
    @access.cookie
    @access.public
    def getHistogram(self, params):
        Image = self.model('image', 'isic_archive')

        query = self._parseFilter(params['filter']) if 'filter' in params else None
        user = self.getCurrentUser()
        return Image.getHistograms(query, user)

    @describeRoute(
        Description('Return an image\'s details.')
        .param('id', 'The ID of the image.', paramType='path')
        .errorResponse('ID was invalid.')
    )
    @access.cookie
    @access.public
    @loadmodel(model='image', plugin='isic_archive', level=AccessType.READ)
    def getImage(self, image, params):
        Dataset = self.model('dataset', 'isic_archive')
        User = self.model('user', 'isic_archive')

        user = self.getCurrentUser()

        output = {
            '_id': image['_id'],
            '_modelType': 'image',
            'name': image['name'],
            'created': image['created'],
            'creator': User.filterSummary(
                User.load(image['creatorId'], force=True, exc=True),
                user),
            # TODO: verify that "updated" is set correctly
            'updated': image['updated'],
            'dataset': Dataset.filterSummary(
                Dataset.load(image['folderId'], force=True, exc=True),
                user),
            'meta': {
                'acquisition': image['meta']['acquisition'],
                'clinical': image['meta']['clinical'],
                'unstructured': image['meta']['unstructured']
            },
            'notes': {
                'reviewed': image['meta'].get('reviewed', None),
                'tags': image['meta']['tags']
            }
        }
        if User.canReviewDataset(user):
            output['meta']['private'] = image['privateMeta']

        return output

    @describeRoute(
        Description('Return an image\'s thumbnail.')
        .param('id', 'The ID of the image.', paramType='path')
        .param('width', 'The desired maximum width for the thumbnail.', paramType='query',
               required=False, default=256)
        .param('height', 'The desired maximum height for the thumbnail.', paramType='query',
               required=False, default=256)
        .errorResponse('ID was invalid.')
    )
    @access.cookie
    @access.public
    @loadmodel(model='image', plugin='isic_archive', level=AccessType.READ)
    def thumbnail(self, image, params):
        ImageItem = self.model('image_item', 'large_image')

        width = int(params.get('width', 256))
        height = int(params.get('height', 256))
        thumbData, thumbMime = ImageItem.getThumbnail(image, width=width, height=height)

        # Only setRawResponse now, as this handler may return a JSON error
        # earlier
        setRawResponse()
        setResponseHeader('Content-Type', thumbMime)
        return thumbData

    @describeRoute(
        Description('Return an image\'s multiresolution tile information.')
        .param('id', 'The ID of the image.', paramType='path')
        .errorResponse('ID was invalid.')
    )
    @access.cookie
    @access.public
    @loadmodel(model='image', plugin='isic_archive', level=AccessType.READ)
    def getTileInfo(self, image, params):
        ImageItem = self.model('image_item', 'large_image')
        # These endpoints should guarantee that large_image functionality works, so a
        # TileGeneralException can be treated as an internal server error and not get caught
        return ImageItem.getMetadata(image)

    @describeRoute(
        Description('Return a multiresolution tile for an image.')
        .param('id', 'The ID of the image.', paramType='path')
        .param('z', 'The layer number of the tile (0 is the most zoomed-out layer).',
               paramType='path')
        .param('x', 'The X coordinate of the tile (0 is the left side).', paramType='path')
        .param('y', 'The Y coordinate of the tile (0 is the top).', paramType='path')
        .errorResponse('ID was invalid.')
    )
    @access.cookie
    @access.public
    @loadmodel(model='image', plugin='isic_archive', level=AccessType.READ)
    def getTile(self, image, z, x, y, params):
        ImageItem = self.model('image_item', 'large_image')
        try:
            x, y, z = int(x), int(y), int(z)
        except ValueError:
            raise RestException('x, y, and z must be integers')
        if x < 0 or y < 0 or z < 0:
            raise RestException('x, y, and z must be positive integers')
        try:
            tileData, tileMime = ImageItem.getTile(image, x, y, z)
        except TileGeneralException as e:
            raise RestException(e.message, code=404)
        setResponseHeader('Content-Type', tileMime)
        setRawResponse()
        return tileData

    @describeRoute(
        Description('Download an image\'s high-quality original binary data.')
        .param('id', 'The ID of the image.', paramType='path')
        .param('contentDisposition',
               'Specify the Content-Disposition response header disposition-type value.',
               required=False, enum=['inline', 'attachment'])
        .errorResponse('ID was invalid.')
    )
    @access.cookie
    @access.public
    @loadmodel(model='image', plugin='isic_archive', level=AccessType.READ)
    def download(self, image, params):
        File = self.model('file')
        Image = self.model('image', 'isic_archive')

        contentDisp = params.get('contentDisposition', None)
        if contentDisp is not None and contentDisp not in {'inline', 'attachment'}:
            raise ValidationException('Unallowed contentDisposition type "%s".' % contentDisp,
                                      'contentDisposition')

        originalFile = Image.originalFile(image)
        fileStream = File.download(originalFile, headers=True, contentDisposition=contentDisp)
        return fileStream

    @describeRoute(
        Description('Get the superpixels for this image, as a PNG-encoded label map.')
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
        .param('seed', 'The X, Y coordinates of a segmentation seed point.', paramType='body')
        .param('tolerance', 'The intensity tolerance value for the segmentation.', paramType='body')
        .errorResponse('ID was invalid.')
    )
    @access.user
    @loadmodel(model='image', plugin='isic_archive', level=AccessType.READ)
    def doSegmentation(self, image, params):
        Segmentation = self.model('segmentation', 'isic_archive')
        params = self._decodeParams(params)
        self.requireParams(['seed', 'tolerance'], params)

        # validate parameters
        seedCoord = params['seed']
        if not (
            isinstance(seedCoord, list) and
            len(seedCoord) == 2 and
            all(isinstance(value, int) for value in seedCoord)
        ):
            raise ValidationException('Value must be a coordinate pair.', 'seed')

        tolerance = params['tolerance']
        if not isinstance(tolerance, int):
            raise ValidationException('Value must be an integer.', 'tolerance')

        try:
            contourCoords = Segmentation.doContourSegmentation(image, seedCoord, tolerance)
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
