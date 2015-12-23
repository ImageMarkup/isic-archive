#!/usr/bin/env python
# -*- coding: utf-8 -*-

import itertools

import numpy
import skimage.io
import skimage.measure
import skimage.morphology

from .base import BaseSegmentationHelper


class ScikitSegmentationHelper(BaseSegmentationHelper):
    @classmethod
    def loadImage(cls, image_data):
        return skimage.io.imread(image_data)

    @classmethod
    def segment(cls, image, seed_coord, tolerance):
        mask_image = cls._floodFill(
            image,
            seed_coord,
            tolerance,
            connectivity=8
        )
        mask_image = cls._binaryOpening(mask_image)
        contour_coords = cls._maskToContour(mask_image)
        return contour_coords


    @classmethod
    def _clippedAdd(cls, array, value):
        type_info = numpy.iinfo(array.dtype)
        new_array = array.astype(int)
        new_array += value
        return new_array.clip(type_info.min, type_info.max).astype(array.dtype)


    @classmethod
    def _floodFill(cls, image, seed_coord, tolerance, connectivity=8):
        seed_value = image[seed_coord[1], seed_coord[0]]
        seed_value_min = cls._clippedAdd(seed_value, -tolerance)
        seed_value_max = cls._clippedAdd(seed_value, tolerance)

        if connectivity == 4:
            connectivity_arg = 1
            pass
        elif connectivity == 8:
            connectivity_arg = 2
        else:
            raise ValueError('Unknown connectivity value.')

        mask_image = skimage.measure.label(
            numpy.all(
                numpy.logical_and(
                    image >= seed_value_min,
                    image <= seed_value_max
                ),
                2
            ).astype(int),
            return_num=False,
            connectivity=connectivity_arg
        )

        mask_image = numpy.equal(
            mask_image, mask_image[seed_coord[1], seed_coord[0]])
        return mask_image


    @classmethod
    def _binaryOpening(cls, image, element_shape='circle', element_radius=5):
        element_size = (element_radius * 2) - 1
        element_type = image.dtype

        if element_shape == 'circle':
            element = skimage.morphology.disk(element_size, element_type)
        elif element_shape == 'cross':
            element = numpy.zeros((element_size, element_size), element_type)
            element[:, element_size // 2] = element_type(True)
            element[element_size // 2, :] = element_type(True)
        elif element_shape == 'square':
            element = skimage.morphology.square(element_size, element_type)
        else:
            raise ValueError('Unknown element shape value.')

        morphed_image = skimage.morphology.binary_opening(
            image=image,
            selem=element
        )
        return morphed_image


    @classmethod
    def _collapseCoords(cls, coords):
        collapsed_coords = [coords[0]]
        collapsed_coords.extend([
            coord
            for prev_coord, coord, next_coord in itertools.izip(coords[0:], coords[1:], coords[2:])
            if numpy.cross(next_coord - prev_coord, coord - prev_coord) != 0
        ])
        collapsed_coords.append(coords[-1])
        collapsed_coords = numpy.array(collapsed_coords)
        return collapsed_coords


    @classmethod
    def _maskToContour(cls, mask_image):
        """
        Extract the contour line within a segmented label mask, using
        Scikit-Image.

        :param mask_image: A binary label mask.
        :type mask_image: numpy.ndarray of bool
        :return: An array of point pairs.
        :rtype: numpy.ndarray
        """
        if mask_image.dtype != bool:
            raise TypeError('mask_image must be an array of bool.')

        coords = skimage.measure.find_contours(
            array=mask_image.astype(numpy.double),
            level=0.5,
            fully_connected='low',
            positive_orientation='low'
        )
        coords = numpy.fliplr(coords[0])
        coords = cls._collapseCoords(coords)
        return coords


    @classmethod
    def _contourToMask(cls, image, coords):
        mask_image = skimage.measure.grid_points_in_poly(
            shape=image.shape[:2],
            verts=numpy.fliplr(coords)
        )
        return mask_image
