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
import os

from bson import ObjectId
from bson.errors import InvalidId
import geojson
import six

from girder.api import access
from girder.api.describe import autoDescribeRoute, describeRoute, Description
from girder.api.rest import loadmodel, setRawResponse, setResponseHeader
from girder.constants import AccessType
from girder.exceptions import GirderException, RestException, ValidationException
from girder.models.file import File
from girder.utility import mail_utils, ziputil
from girder_large_image.models.image_item import ImageItem
from large_image.exceptions import TileGeneralException

from .base import IsicResource
from ..models.dataset import Dataset
from ..models.image import Image
from ..models.segmentation import Segmentation
from ..models.user import User
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
        self.route('POST', (':id', 'metadata'), self.applyMetadata)

    def _parseFilter(self, filterParam):
        if isinstance(filterParam, six.string_types):
            try:
                filterParam = json.loads(filterParam)
            except ValueError as e:
                raise ValidationException('Could not decode JSON: %s' % str(e), 'filter')
        try:
            return querylang.astToMongo(filterParam)
        except (TypeError, ValueError, InvalidId) as e:
            raise ValidationException('Could not parse filter: %s' % str(e), 'filter')

    def _parseImageIds(self, imageIdsParam):
        if isinstance(imageIdsParam, six.string_types):
            try:
                imageIdsParam = json.loads(imageIdsParam)
            except ValueError as e:
                raise ValidationException('Could not decode JSON: %s' % str(e), 'imageIds')
        if not isinstance(imageIdsParam, list):
            raise ValidationException('"imageIds" must be a JSON-encoded array.', 'imageIds')
        if len(imageIdsParam) > 300:
            raise ValidationException('"imageIds" may not contain more than 300 IDs.', 'imageIds')
        imageIds = []
        for imageId in imageIdsParam:
            if not isinstance(imageId, six.string_types):
                raise ValidationException('Each of "imageIds" must be a string.', 'imageIds')
            try:
                imageId = ObjectId(imageId)
            except InvalidId:
                raise ValidationException('Invalid ObjectId.', 'imageIds')
            imageIds.append(imageId)
        # TODO: We could validate that the user has access to all of the requested IDs, and
        # raise a 403 error if now. Currently, we will silently exclude images that the user doesn't
        # have permission to READ.

        query = {
            '_id': {'$in': imageIds}
        }
        return query

    @describeRoute(
        Description('Return a list of lesion images.')
        .pagingParams(defaultSort='name')
        .param('detail', 'Display the full information for each image, instead of a summary.',
               required=False, dataType='boolean', default=False)
        .param('name', 'Find an image with a specific name.', required=False)
        .param('filter', 'Filter the images by a PegJS-specified grammar.',
               required=False)
        .param('imageIds',
               'A JSON array of up to 300 image IDs, which will be exclusively included.',
               required=False)
        .errorResponse()
    )
    @access.cookie
    @access.public
    def find(self, params):
        user = self.getCurrentUser()
        detail = self.boolParam('detail', params, default=False)
        limit, offset, sort = self.getPagingParameters(params, 'name')

        if sum(option in params for option in {'name', 'filter', 'imageIds'}) > 1:
            raise RestException('Only one of "name", "filter", or "imageIds" may be specified.')

        if 'name' in params:
            query = {'name': params['name']}
        elif 'filter' in params:
            query = self._parseFilter(params['filter'])
        elif 'imageIds' in params:
            query = self._parseImageIds(params['imageIds'])
        else:
            query = {}
        # Exclude images that haven't passed QC review (though they can still be accessed by more
        # direct endpoints if the user has permission)
        query.update({
            'meta.reviewed.accepted': True
        })

        filterFunc = Image().filter if detail else Image().filterSummary
        return [
            filterFunc(image, user)
            for image in
            Image().filterResultsByPermission(
                Image().find(query, sort=sort),
                user=user, level=AccessType.READ, limit=limit, offset=offset)
        ]

    def _imagesZipGenerator(self, downloadFileName, images, include):
        datasetCache = {}
        zipGenerator = ziputil.ZipGenerator(downloadFileName)

        for image in images:
            datasetId = image['meta']['datasetId']
            if datasetId not in datasetCache:
                datasetCache[datasetId] = Dataset().load(datasetId, force=True, exc=True)
            dataset = datasetCache[datasetId]

            if include in {'all', 'images'}:
                imageFile = Image().originalFile(image)
                imageFileGenerator = File().download(imageFile, headers=False)
                for data in zipGenerator.addFile(
                        imageFileGenerator,
                        path=os.path.join(dataset['name'], imageFile['name'])):
                    yield data
            if include in {'all', 'metadata'}:
                def metadataGenerator():
                    # TODO: Consider replacing this with Image().filter
                    yield json.dumps({
                        '_id': str(image['_id']),
                        'name': image['name'],
                        'meta': {
                            'acquisition': image['meta']['acquisition'],
                            'clinical': image['meta']['clinical']
                        }
                    })
                for data in zipGenerator.addFile(
                        metadataGenerator,
                        path=os.path.join(dataset['name'], '%s.json' % image['name'])):
                    yield data

        for dataset in six.viewvalues(datasetCache):
            licenseText = mail_utils.renderTemplate(
                'license_%s.mako' % dataset['license'])
            attributionText = mail_utils.renderTemplate(
                'attribution_%s.mako' % dataset['license'],
                {
                    'work': dataset['name'],
                    'author': dataset['attribution']
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

    @describeRoute(
        Description('Download multiple images as a ZIP file.')
        .param('include', 'Which types of data to include.', required=False,
               enum=['all', 'images', 'metadata'], default='all')
        .param('filter', 'Filter the images by a PegJS-specified grammar.',
               required=False)
        .param('imageIds',
               'A JSON array of up to 300 image IDs, which will be exclusively included.',
               required=False)
        .produces('application/zip')
        .errorResponse()
    )
    @access.cookie
    @access.public
    def downloadMultiple(self, params):
        include = params.get('include', 'all')
        if include not in {'all', 'images', 'metadata'}:
            raise ValidationException(
                'Param "include" must be one of: "all", "images", "metadata"', 'include')

        if 'filter' in params and 'imageIds' in params:
            raise RestException('Only one of "filter" or "imageIds" may be specified.')

        if 'filter' in params:
            query = self._parseFilter(params['filter'])
        elif 'imageIds' in params:
            query = self._parseImageIds(params['imageIds'])
        else:
            query = {}

        user = self.getCurrentUser()
        downloadFileName = 'ISIC-images'

        images = Image().filterResultsByPermission(
            Image().find(query, sort=[('name', 1)]),
            user=user, level=AccessType.READ, limit=0, offset=0)
        # Prevent cursor timeouts by eagerly evaluating the whole query
        images = list(images)
        imagesZipGenerator = self._imagesZipGenerator(downloadFileName, images, include)

        setResponseHeader('Content-Type', 'application/zip')
        setResponseHeader('Content-Disposition', 'attachment; filename="%s.zip"' % downloadFileName)
        return lambda: imagesZipGenerator

    @describeRoute(
        Description('Return histograms of image metadata.')
        .param('filter', 'Filter the images by a PegJS-specified grammar.', required=False)
        .errorResponse()
    )
    @access.cookie
    @access.public
    def getHistogram(self, params):
        query = self._parseFilter(params['filter']) if 'filter' in params else None
        user = self.getCurrentUser()
        return Image().getHistograms(query, user)

    @describeRoute(
        Description('Return an image\'s details.')
        .param('id', 'The ID of the image.', paramType='path')
        .errorResponse('ID was invalid.')
    )
    @access.cookie
    @access.public
    @loadmodel(model='image', plugin='isic_archive', level=AccessType.READ)
    def getImage(self, image, params):
        user = self.getCurrentUser()
        return Image().filter(image, user)

    @describeRoute(
        Description('Return an image\'s thumbnail.')
        .param('id', 'The ID of the image.', paramType='path')
        .param('width', 'The desired maximum width for the thumbnail.', paramType='query',
               required=False, default=256)
        .param('height', 'The desired maximum height for the thumbnail.', paramType='query',
               required=False, default=256)
        .produces('image/jpeg')
        .errorResponse('ID was invalid.')
    )
    @access.cookie
    @access.public
    @loadmodel(model='image', plugin='isic_archive', level=AccessType.READ)
    def thumbnail(self, image, params):
        width = int(params.get('width', 256))
        height = int(params.get('height', 256))
        thumbData, thumbMime = ImageItem().getThumbnail(image, width=width, height=height)

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
        # These endpoints should guarantee that large_image functionality works, so a
        # TileGeneralException can be treated as an internal server error and not get caught
        return ImageItem().getMetadata(image)

    @describeRoute(
        Description('Return a multiresolution tile for an image.')
        .param('id', 'The ID of the image.', paramType='path')
        .param('z', 'The layer number of the tile (0 is the most zoomed-out layer).',
               paramType='path')
        .param('x', 'The X coordinate of the tile (0 is the left side).', paramType='path')
        .param('y', 'The Y coordinate of the tile (0 is the top).', paramType='path')
        .produces('image/jpeg')
        .errorResponse('ID was invalid.')
    )
    @access.cookie
    @access.public
    @loadmodel(model='image', plugin='isic_archive', level=AccessType.READ)
    def getTile(self, image, z, x, y, params):
        try:
            x, y, z = int(x), int(y), int(z)
        except ValueError:
            raise RestException('x, y, and z must be integers')
        if x < 0 or y < 0 or z < 0:
            raise RestException('x, y, and z must be positive integers')
        try:
            tileData, tileMime = ImageItem().getTile(image, x, y, z)
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
        .produces(['image/jpeg', 'image/png', 'image/bmp'])
        .errorResponse('ID was invalid.')
    )
    @access.cookie
    @access.public
    @loadmodel(model='image', plugin='isic_archive', level=AccessType.READ)
    def download(self, image, params):
        contentDisp = params.get('contentDisposition', None)
        if contentDisp is not None and contentDisp not in {'inline', 'attachment'}:
            raise ValidationException('Unallowed contentDisposition type "%s".' % contentDisp,
                                      'contentDisposition')

        originalFile = Image().originalFile(image)
        fileStream = File().download(originalFile, headers=True, contentDisposition=contentDisp)
        return fileStream

    @describeRoute(
        Description('Get the superpixels for this image, as a PNG-encoded label map.')
        .param('id', 'The ID of the image.', paramType='path')
        .produces('image/png')
        .errorResponse('ID was invalid.')
    )
    @access.cookie
    @access.public
    @loadmodel(model='image', plugin='isic_archive', level=AccessType.READ)
    def getSuperpixels(self, image, params):
        superpixelsFile = Image().superpixelsFile(image)
        return File().download(superpixelsFile, headers=True)

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
            contourCoords = Segmentation().doContourSegmentation(image, seedCoord, tolerance)
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

    @autoDescribeRoute(
        Description('Apply metadata to an image.')
        .notes('Validates and adds acquisition and clinical metadata to an image.\n'
               'The `metadata` parameter is a JSON object which contains a name/value pair '
               'for each field to add or update. The object should not contain nested structures.'
               '\n\n'
               'Example:\n'
               '```\n'
               '{\n'
               '    "age": 45,\n'
               '    "sex": "male",\n'
               '    "benign_malignant": "malignant",\n'
               '    "diagnosis": "melanoma",\n'
               '    "diagnosis_confirm_type": "histopathology",\n'
               '    "mel_class": "melanoma NOS",\n'
               '    "mel_mitotic_index": "2/mm^2",\n'
               '    "mel_thick_mm": "1.5 mm",\n'
               '    "mel_type": "melanoma NOS",\n'
               '    "mel_ulcer": "true"\n'
               '}\n'
               '```\n'
               'Returns an object that has two fields: `errors` and `warnings`. Each contains a '
               'list of objects that have a `description` field, which is a user-readable '
               'string describing the error or warning.'
               '\n\n'
               'Validation is successful when the `errors` list is empty. Otherwise, the metadata '
               'is not saved, regardless of the value of the `save` parameter, and the `errors` '
               'list contains the validation errors. Validation can fail for several reasons, '
               'including but not limited to:\n'
               '- The value of a field is of the wrong type\n'
               '- The values of two or more fields are inconsistent with one another\n'
               '- A value of a field already exists and cannot be safely overwritten\n'
               '\n'
               'When there are no errors, the `warnings` list contains warnings that don\'t '
               'prevent saving the metadata, but should be reviewed.')
        .modelParam('id', description='The ID of the image.', model=Image, destName='image',
                    level=AccessType.READ)
        .jsonParam('metadata', 'The JSON object containing image metadata.', paramType='body',
                   requireObject=True)
        .param('save', 'Whether to save the metadata to the image if validation succeeds.',
               dataType='boolean', default=False)
        .errorResponse(('ID was invalid.',
                        'Invalid JSON passed in request body.'))
    )
    @access.user
    def applyMetadata(self, image, metadata, save):
        user = self.getCurrentUser()
        User().requireCreateDataset(user)

        # Require write access to image's dataset
        Dataset().load(image['meta']['datasetId'], user=user, level=AccessType.WRITE, exc=True)

        errors, warnings = Image().applyMetadata(image, metadata, save)

        return {
            'errors': [{'description': description} for description in errors],
            'warnings': [{'description': description} for description in warnings]
        }
