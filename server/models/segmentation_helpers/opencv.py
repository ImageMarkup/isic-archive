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

import cv2
import numpy

from .base import BaseSegmentationHelper


class OpenCVSegmentationHelper(BaseSegmentationHelper):
    @classmethod
    def loadImage(cls, imageDataStream):
        """
        Load an image into an RGB array.
        :param imageDataStream: A file-like object containing the encoded
        (JPEG, etc.) image data.
        :type imageDataStream: file-like object
        :return: A Numpy array with the RGB image data.
        :rtype: numpy.ndarray
        """
        if hasattr(imageDataStream, 'getvalue'):
            # This is more efficient for BytesIO objects
            imageDataBytes = imageDataStream.getvalue()
        elif hasattr(imageDataStream, 'read'):
            imageDataBytes = imageDataStream.read()
        else:
            raise ValueError('imageDataStream must be a file-like object.')

        imageDataArray = numpy.fromstring(imageDataBytes, dtype=numpy.uint8)
        del imageDataBytes
        imageData = cv2.imdecode(imageDataArray, cv2.CV_LOAD_IMAGE_COLOR)
        if imageData.shape[2] == 4:
            imageData = imageData[:, :, :3]
        # OpenCV loads images as BGR, and cv2.floodFill doesn't work correctly
        #   with array views
        imageData = imageData[:, :, ::-1].copy()
        return imageData

    @classmethod
    def writeImage(cls, image, encoding='png'):
        # TODO: cv2.imencode
        raise NotImplementedError()

    @classmethod
    def segment(cls, image, seedCoord, tolerance):
        """
        Do a flood-fill segmentation of an image, yielding a single contiguous
        region with no holes.

        :param image: A Numpy array with the image to be segmented.
        :type image: numpy.ndarray
        :param seedCoord: (X, Y) coordinates of the segmentation seed point.
        :type seedCoord: tuple[int]
        :param tolerance: The intensity tolerance value for the segmentation.
        :type tolerance: int
        :return: The mask image of the segmented region, with values 0 or 255.
        :rtype: numpy.ndarray
        """
        maskImage = cls._floodFill(
            image,
            seedCoord,
            tolerance,
            # Leaving padOutput allows the next operation to reach around
            # edge-touching components
            padOutput=True)

        # Now, fill in any holes in the maskImage
        maskImageBackground = cls._floodFill(
            maskImage,
            # The seed point is a part of the padded border of maskImage
            seedCoord=(0, 0),
            # The seed point and border will have a value of 1, but we want to
            # also include the actual mask background, which has a value of 0
            tolerance=1,
            # A second additional layer of padding is not required
            padOutput=False)
        # Remove the extra padding
        maskImageBackground = maskImageBackground[1:-1, 1:-1]
        # Flip the background, to get the mask with holes removed
        maskImage = numpy.invert(maskImageBackground)

        return maskImage

    @classmethod
    def _floodFill(cls, image, seedCoord, tolerance, connectivity=8,
                   padOutput=False):
        """
        Segment an image into a region connected to a seed point, using OpenCV.

        :param image: The image to be segmented.
        :type image: numpy.ndarray
        :param seedCoord: The point inside the connected region where the
        segmentation will start.
        :type seedCoord: tuple[int]
        :param tolerance: The maximum color/intensity difference between the
        seed point and a point in the connected region.
        :type tolerance: int
        :param connectivity: (optional) The number of allowed connectivity
        propagation directions. Allowed values are:
          * 4 for edge pixels
          * 8 for edge and corner pixels
        :type connectivity: int
        :param padOutput: (optional)  Return the output with a 1-pixel wide
        padded border.
        :type padOutput: bool
        :returns: A binary label mask, with an extra 1-pixel wide padded border.
        The values are either ``0`` or ``fillValue``.
        :rtype: numpy.ndarray
        """
        # create padded mask to store output
        maskImage = numpy.zeros(
            image.shape[:2] + numpy.array([2, 2]), numpy.uint8)
        fillValue = 255

        flags = 0
        flags |= connectivity
        flags |= (fillValue << 8)  # fill value is
        # compare each candidate to the seed, not its nearest neighbor; for
        #   lesion images, the gradient is too shallow for even very small
        #   tolerances to work with a nearest neighbor comparison
        flags |= cv2.FLOODFILL_FIXED_RANGE
        flags |= cv2.FLOODFILL_MASK_ONLY

        area, (boundsX, boundsY, boundsWidth, boundsHeight) = cv2.floodFill(
            image=image,
            mask=maskImage,
            seedPoint=tuple(seedCoord),
            newVal=(0,) * 3,  # this is ignored, due to FLOODFILL_MASK_ONLY
            loDiff=(tolerance,) * 3,
            upDiff=(tolerance,) * 3,
            flags=flags)

        if not padOutput:
            maskImage = maskImage[1:-1, 1:-1]

        return maskImage

    @classmethod
    def _structuringElement(cls, shape, radius, elementType=bool):
        size = (radius * 2) + 1

        if shape == 'circle':
            # This is broken and does not return a true circle, but there is
            #   no way to change the major/semi-major axes
            shapeKey = cv2.MORPH_ELLIPSE
        elif shape == 'cross':
            shapeKey = cv2.MORPH_CROSS
        elif shape == 'square':
            shapeKey = cv2.MORPH_RECT
        else:
            raise ValueError('Unknown element shape value.')

        element = cv2.getStructuringElement(shapeKey, (size, size))
        return element.astype(elementType)

    @classmethod
    def _binaryOpening(cls, image, elementShape='circle', elementRadius=5,
                       padded_input=False):
        if image.dtype != numpy.uint8:
            raise TypeError('image must be an array of uint8.')

        # This is the only version that returns a true circle
        from .scikit import ScikitSegmentationHelper
        element = ScikitSegmentationHelper._structuringElement(
            elementShape, elementRadius, image.dtype.type)

        morphedImage = cv2.morphologyEx(
            src=image,
            op=cv2.MORPH_OPEN,
            kernel=element
        )

        if padded_input:
            morphedImage[[0, -1], :] = 1
            morphedImage[:, [0, -1]] = 1

        return morphedImage

    @classmethod
    def _maskToContours(cls, maskImage, paddedInput=False, safe=True):
        """
        Extract the contour lines within a segmented label mask, using OpenCV.

        :param maskImage: A binary label mask. Values are considered as only 0
        or non-0.
        :type maskImage: numpy.ndarray of numpy.uint8
        :param paddedInput: Whether the mask_image already includes a 1-pixel
        wide padded border.
        :type paddedInput: bool
        :param safe: Guarantee that the image_mask will not be modified. This is
        slower.
        :type safe: bool
        :return: An array of point pairs.
        :rtype: numpy.ndarray
        """
        if maskImage.dtype != numpy.uint8:
            raise TypeError('maskImage must be an array of uint8.')

        if not paddedInput:
            paddedMaskImage = numpy.zeros(
                maskImage.shape + numpy.array([2, 2]),
                maskImage.dtype
            )
            paddedMaskImage[1:-1, 1:-1] = maskImage
            maskImage = paddedMaskImage
            del paddedMaskImage
        elif safe:
            maskImage = numpy.copy(maskImage)

        contours, hierarchy = cv2.findContours(
            image=maskImage,
            mode=cv2.RETR_EXTERNAL,
            method=cv2.CHAIN_APPROX_SIMPLE,
            # compensate for the image's 1-pixel padding
            offset=(-1, -1)
        )

        # each contour initially looks like [ [[0,1]], [[0,2]] ], so squeeze it
        # note, don't use numpy.squeeze, as that will break singleton contours
        contours = map(
            lambda contour: contour[:, 0],
            contours)

        # place a duplicate of the first value at the end
        contours = map(
            lambda contour: numpy.append(contour, contour[0:1], axis=0),
            contours)

        return contours

    @classmethod
    def maskToContour(cls, maskImage, paddedInput=False, safe=True):
        """
        Extract the longest contour line within a segmented label mask,
        using OpenCV.
        """
        contours = cls._maskToContours(maskImage, paddedInput, safe)

        # Morphological operations may cause multiple disconnected components;
        #   ideally, the seed point + region growing would be used to eliminate
        #   these, but this is slower and the seed point is not available for
        #   many older segmentations; so, simply select the largest component
        #   instead
        largestContour = max(
            contours,
            # TODO: use a better measure of region size than simply the number
            #   of defining points
            key=lambda contour: len(contour)
        )

        return largestContour
