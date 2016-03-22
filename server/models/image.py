#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
import six

import geojson

from girder.constants import AccessType
from girder.models.model_base import AccessException, GirderException
from girder.models.item import Item

from .. import constants
from ..provision_utility import _ISICCollection
from .segmentation_helpers import ScikitSegmentationHelper, \
    OpenCVSegmentationHelper


class Image(Item):

    def initialize(self):
        super(Image, self).initialize()

        self._filterKeys[AccessType.READ].clear()
        self.exposeFields(level=AccessType.READ, fields=(
            '_id', 'name', 'description', 'meta', 'created', 'creatorId',
            'updated',
            # TODO: re-add once converted file no longer contributes to size
            # 'size',
        ))

        self.summaryFields = ('_id', 'name', 'updated')


    def createImage(self, creator, parentFolder):
        new_isic_id = self.model('setting').get(
            constants.PluginSettings.MAX_ISIC_ID, default=-1) + 1

        image = self.createItem(
            name='ISIC_%07d' % new_isic_id,
            creator=creator,
            folder=parentFolder,
            description=''
        )
        self.setMetadata(image, {
            'clinical': {},
            'acquisition': {}
        })

        self.model('setting').set(
            constants.PluginSettings.MAX_ISIC_ID, new_isic_id)

        return image


    def originalFile(self, image):
        return self.model('file').findOne({
            'itemId': image['_id'],
            # TODO: make this more robust (original image may not be a JPEG)
            'name': '%s.jpg' % image['name']
        })


    def imageData(self, image):
        """
        Return the RGB image data associated with this image.

        :rtype: numpy.ndarray
        """
        image_file = self.originalFile(image)

        image_file_stream = six.BytesIO()
        image_file_stream.writelines(
            self.model('file').download(image_file, headers=False)()
        )

        # Scikit-Image is ~70ms faster at loading images
        image_data = ScikitSegmentationHelper.loadImage(image_file_stream)
        return image_data


    def flag(self, image, reason, user):
        self.flagMultiple([image], reason, user)


    def flagMultiple(self, images, reason, user):
        # TODO: change to use direct permissions on the images
        if not any(
            self.model('group').findOne(
                {'name': groupName}
            )['_id'] in user.get('groups', [])
            for groupName in
            ['Phase 0', 'Phase 1a', 'Phase 1b']
        ):
            # Check if all images are part of annotation studies that this user
            #   is part of
            image_ids = list(set(image['_id'] for image in images))
            annotations = self.model('annotation', 'isic_archive').find({
                'imageId': {'$in': image_ids},
                'userId': user['_id']
            })
            if len(image_ids) != len(annotations):
                raise AccessException(
                    'User does not have permission to flag these images.')

        datasets = [
            self.model('dataset', 'isic_archive').load(
                dataset_id, force=True)
            for dataset_id in
            set(image['folderId'] for image in images)
        ]

        flagged_collection = self.model('collection').findOne(
            {'name': 'Flagged Images'})

        dataset_flagged_folders = {
            dataset['_id']: _ISICCollection.createFolder(
                name=dataset['name'],
                description='',
                parent=flagged_collection,
                parent_type='collection'
            )
            for dataset in datasets
        }

        flag_metadata = {
            'flaggedUserId': user['_id'],
            'flaggedTime': datetime.datetime.utcnow(),
            'flaggedReason': reason,
        }
        for image in images:
            self.model('item').setMetadata(image, flag_metadata)
            # TODO: deal with any existing studies with this image
            self.model('item').move(image, dataset_flagged_folders[image['folderId']])


    def doSegmentation(self, image, seed_coord, tolerance):
        """
        Run a lesion segmentation.

        :param image: A Girder Image item.
        :param seed_coord: X, Y coordinates of the segmentation seed point.
        :type seed_coord: tuple[int]
        :param tolerance: The intensity tolerance value for the segmentation.
        :type tolerance: int
        :return: The lesion segmentation, as a GeoJSON Polygon Feature.
        :rtype: geojson.Feature
        """
        image_data = self.imageData(image)

        if not(
            # The image_data has a shape of (rows, cols), the seed is (x, y)
            0.0 <= seed_coord[0] <= image_data.shape[1] and
            0.0 <= seed_coord[1] <= image_data.shape[0]
        ):
            raise GirderException('seed_coord is out of bounds')

        # OpenCV is significantly faster at segmentation right now
        contour_coords = OpenCVSegmentationHelper.segment(
            image_data, seed_coord, tolerance)

        contour_feature = geojson.Feature(
            geometry=geojson.Polygon(
                coordinates=(contour_coords.tolist(),)
            ),
            properties={
                'source': 'autofill',
                'seedPoint': seed_coord,
                'tolerance': tolerance
            }
        )

        return contour_feature


    def validate(self, doc):
        # TODO: implement
        # raise ValidationException
        return Item.validate(self, doc)
