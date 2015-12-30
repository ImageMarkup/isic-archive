#!/usr/bin/env python
# -*- coding: utf-8 -*-

import cv2
import numpy

from .base import BaseSegmentationHelper


class OpenCVSegmentationHelper(BaseSegmentationHelper):
    @classmethod
    def loadImage(cls, image_data_stream):
        """
        Load an image into an RGB array.
        :param image_data_stream: A file-like object containing the encoded
        (JPEG, etc.) image data.
        :type image_data_stream: file-like object
        :return: A Numpy array with the RGB image data.
        :rtype: numpy.ndarray
        """
        if hasattr(image_data_stream, 'getvalue'):
            # This is more efficient for BytesIO objects
            image_data_bytes = image_data_stream.getvalue()
        elif hasattr(image_data_stream, 'read'):
            image_data_bytes = image_data_stream.read()
        else:
            raise ValueError('image_data_stream must be a file-like object.')

        image_data_array = numpy.fromstring(image_data_bytes, dtype=numpy.uint8)
        del image_data_bytes
        image_data = cv2.imdecode(image_data_array, cv2.CV_LOAD_IMAGE_COLOR)
        # OpenCV loads images as BGR, and cv2.floodFill doesn't work correctly
        #   with array views
        image_data = image_data[:, :, ::-1].copy()
        return image_data


    @classmethod
    def writeImage(cls, image, encoding='png'):
        # TODO: cv2.imencode
        raise NotImplementedError()


    @classmethod
    def segment(cls, image, seed_coord, tolerance):
        mask_image = cls._floodFill(
            image,
            seed_coord,
            tolerance,
            connectivity=8,
            pad_output=True
        )
        # TODO: for _binaryOpening to work, a new _floodFill must be run on the
        #   mask image afterwards, or else _maskToContour will fail
        # mask_image = cls._binaryOpening(mask_image, padded_input=True)
        contour_coords = cls._maskToContour(
            mask_image,
            padded_input=True,
            safe=False
        )
        return contour_coords


    @classmethod
    def _floodFill(cls, image, seed_coord, tolerance, connectivity=8,
                   pad_output=False):
        """
        Segment an image into a region connected to a seed point, using OpenCV.

        :param image: The image to be segmented.
        :type image: numpy.ndarray
        :param seed_coord: The point inside the connected region where the
        segmentation will start.
        :type seed_coord: list
        :param tolerance: The maximum color/intensity difference between the
        seed point and a point in the connected region.
        :type tolerance: int
        :param connectivity: (optional) The number of allowed connectivity
        propagation directions. Allowed values are:
          * 4 for edge pixels
          * 8 for edge and corner pixels
        :type connectivity: int
        :param pad_output: (optional)  Return the output with a 1-pixel wide
        padded border.
        :type pad_output: bool
        :returns: A binary label mask, with an extra 1-pixel wide padded border.
        The values are either ``0`` or ``fill_value``.
        :rtype: numpy.ndarray
        """
        # create padded mask to store output
        mask_image = numpy.zeros(
            image.shape[:2] + numpy.array([2, 2]), numpy.uint8)
        fill_value = 1

        flags = 0
        flags |= connectivity
        flags |= (fill_value << 8)  # fill value is
        # compare each candidate to the seed, not its nearest neighbor; for
        #   lesion images, the gradient is too shallow for even very small
        #   tolerances to work with a neared neighbor comparison
        flags |= cv2.FLOODFILL_FIXED_RANGE
        flags |= cv2.FLOODFILL_MASK_ONLY

        area, (bounds_x, bounds_y, bounds_width, bounds_height) = cv2.floodFill(
            image=image,
            mask=mask_image,
            seedPoint=tuple(seed_coord),
            newVal=(0,) * 3,  # this is ignored, due to FLOODFILL_MASK_ONLY
            loDiff=(tolerance,) * 3,
            upDiff=(tolerance,) * 3,
            flags=flags
        )

        if not pad_output:
            mask_image = mask_image[1:-1, 1:-1]

        return mask_image


    @classmethod
    def _binaryOpening(cls, image, element_shape='circle', element_radius=5,
                       padded_input=False):
        if image.dtype != numpy.uint8:
            raise TypeError('image must be an array of uint8.')

        element_size = (element_radius * 2) + 1

        if element_shape == 'circle':
            shape = cv2.MORPH_ELLIPSE
        elif element_shape == 'cross':
            shape = cv2.MORPH_CROSS
        elif element_shape == 'square':
            shape = cv2.MORPH_RECT
        else:
            raise ValueError('Unknown element shape value.')

        morphed_image = cv2.morphologyEx(
            src=image,
            op=cv2.MORPH_OPEN,
            kernel=cv2.getStructuringElement(
                shape, (element_size, element_size))
        )

        if padded_input:
            morphed_image[[0, -1], :] = 1
            morphed_image[:, [0, -1]] = 1

        return morphed_image


    @classmethod
    def _maskToContour(cls, mask_image, padded_input=False, safe=True):
        """
        Extract the contour line within a segmented label mask, using OpenCV.

        :param mask_image: A binary label mask. Values are considered as only 0
        or non-0.
        :type mask_image: numpy.ndarray of numpy.uint8
        :param padded_input: Whether the mask_image already includes a 1-pixel
        wide padded border.
        :type padded_input: bool
        :param safe: Guarantee that the image_mask will not be modified. This is
        slower.
        :type safe: bool
        :return: An array of point pairs.
        :rtype: numpy.ndarray
        """
        if mask_image.dtype != numpy.uint8:
            raise TypeError('mask_image must be an array of uint8.')

        if not padded_input:
            padded_mask_image = numpy.zeros(
                mask_image.shape + numpy.array([2, 2]),
                mask_image.dtype
            )
            padded_mask_image[1:-1, 1:-1] = mask_image
            mask_image = padded_mask_image
            del padded_mask_image
        elif safe:
            mask_image = numpy.copy(mask_image)

        contours, hierarchy = cv2.findContours(
            image=mask_image,
            mode=cv2.RETR_EXTERNAL,
            method=cv2.CHAIN_APPROX_SIMPLE,
            # compensate for the image's 1-pixel padding
            offset=(-1, -1)
        )

        # "cv2.RETR_EXTERNAL" means there's only one contour
        contour = contours[0]
        # contour initially looks like [ [[0,1]], [[0,2]] ], so squeeze it
        contour = numpy.squeeze(contour)
        # place a duplicate of the first value at the end
        contour = numpy.append(contour, contour[0:1], axis=0)
        return contour
