import collections
import io
from typing import BinaryIO, Tuple, Union
import warnings

import numpy
import skimage.io
import skimage.measure
import skimage.morphology
import skimage.segmentation
import skimage.transform

from .base import BaseSegmentationHelper


class ScikitSegmentationHelper(BaseSegmentationHelper):
    @classmethod
    def loadImage(cls, imageDataStream: Union[BinaryIO, str]) -> numpy.ndarray:
        """
        Load an image into an RGB array.

        :param imageDataStream: A file-like object containing the encoded
        (JPEG, etc.) image data or a file path.
        :return: A Numpy array with the RGB image data.
        """
        imageData = skimage.io.imread(imageDataStream, plugin='pil')

        if len(imageData.shape) == 1 and imageData.shape[0] > 1:
            # Some images seem to have a 2nd (or 3rd+) layer, which should be ignored
            # https://github.com/scikit-image/scikit-image/issues/2154
            # The first element within the result should be the main image
            imageData = imageData[0]

        if len(imageData.shape) == 3 and imageData.shape[2] == 4:
            # cv2.floodFill doesn't work correctly with array views, so copy
            imageData = imageData[:, :, :3].copy()
        return imageData

    @classmethod
    def writeImage(cls, image, encoding='png', width=None):
        if width is not None:
            factor = float(width) / image.shape[1]
            image = skimage.transform.rescale(image, factor)

        imageStream = io.BytesIO()
        with warnings.catch_warnings():
            # Ignore warnings about low contrast images, as masks are often empty
            warnings.filterwarnings('ignore', r'^.* is a low contrast image$', UserWarning)
            # The 'pil' plugin is about 40% faster than the default 'imageio' plugin
            # The 'pil' plugin uses 'format_str' as an argument, not 'format'
            skimage.io.imsave(imageStream, image, plugin='pil', format_str=encoding)
        imageStream.seek(0)
        return imageStream

    @classmethod
    def segment(cls, image: numpy.ndarray, seedCoord: Tuple[int, int], tolerance: int
                ) -> numpy.ndarray:
        """
        Do a flood-fill segmentation of an image, yielding a single contiguous region with no holes.

        :param image: A Numpy array with the image to be segmented.
        :param seedCoord: (X, Y) coordinates of the segmentation seed point.
        :param tolerance: The intensity tolerance value for the segmentation.
        :return: The mask image of the segmented region, with values 0 or 255.
        """
        maskImage = cls._floodFill(
            image,
            seedCoord,
            tolerance)

        # Now, fill in any holes in the maskImage
        # First, add a padded border, allowing the next operation to reach
        # around edge-touching components
        maskImage = numpy.pad(maskImage, 1, 'constant', constant_values=1)
        maskImageBackground = cls._floodFill(
            maskImage,
            # The seed point is a part of the padded border of maskImage
            seedCoord=(0, 0),
            # The seed point and border will have a value of 1, but we want to
            # also include the actual mask background, which has a value of 0
            tolerance=1)
        # Remove the extra padding
        maskImageBackground = maskImageBackground[1:-1, 1:-1]
        # Flip the background, to get the mask with holes removed
        maskImage = numpy.invert(maskImageBackground)

        return maskImage

    @classmethod
    def _clippedAdd(cls, array, value):
        typeInfo = numpy.iinfo(array.dtype)
        newArray = array.astype(int)
        newArray += value
        return newArray.clip(typeInfo.min, typeInfo.max).astype(array.dtype)

    @classmethod
    def _floodFill(
            cls, image: numpy.ndarray, seedCoord: Tuple[int, int], tolerance: int,
            connectivity: int = 8) -> numpy.ndarray:
        """
        Segment an image into a region connected to a seed point, using OpenCV.

        :param image: The image to be segmented.
        :param seedCoord: The point inside the connected region where the
        segmentation will start.
        :param tolerance: The maximum color/intensity difference between the
        seed point and a point in the connected region.
        :param connectivity: (optional) The number of allowed connectivity
        propagation directions. Allowed values are:
          * 4 for edge pixels
          * 8 for edge and corner pixels
        :returns: A binary label mask, with an extra 1-pixel wide padded border.
        The values are either ``0`` or ``fillValue``.
        """
        seedValue = image[seedCoord[1], seedCoord[0]]
        seedValueMin = cls._clippedAdd(seedValue, -tolerance)
        seedValueMax = cls._clippedAdd(seedValue, tolerance)

        if connectivity == 4:
            connectivityArg = 1
        elif connectivity == 8:
            connectivityArg = 2
        else:
            raise ValueError('Unknown connectivity value.')

        binaryImage = numpy.logical_and(
            image >= seedValueMin,
            image <= seedValueMax
        )
        if len(image.shape) == 3:
            # Reduce RGB components, requiring all to be within threshold
            binaryImage = numpy.all(binaryImage, 2)

        labelImage = skimage.measure.label(
            binaryImage.astype(int),
            return_num=False,
            connectivity=connectivityArg
        )
        del binaryImage

        maskImage = numpy.equal(
            labelImage, labelImage[seedCoord[1], seedCoord[0]])
        del labelImage
        maskImage = maskImage.astype(numpy.uint8) * 255

        return maskImage

    @classmethod
    def _structuringElement(cls, shape, radius, elementType=bool):
        size = (radius * 2) + 1

        if shape == 'circle':
            element = skimage.morphology.disk(radius, elementType)
        elif shape == 'cross':
            element = numpy.zeros((size, size), elementType)
            element[:, size // 2] = elementType(True)
            element[size // 2, :] = elementType(True)
        elif shape == 'square':
            element = skimage.morphology.square(size, elementType)
        else:
            raise ValueError('Unknown element shape value.')

        return element

    @classmethod
    def _binaryOpening(cls, image, elementShape='circle', elementRadius=5):
        element = cls._structuringElement(elementShape, elementRadius, bool)

        morphedImage = skimage.morphology.binary_opening(
            image=image,
            selem=element
        )
        return morphedImage

    @classmethod
    def _collapseCoords(cls, coords):
        collapsedCoords = [coords[0]]
        collapsedCoords.extend([
            coord
            for prevCoord, coord, nextCoord in zip(
                coords[0:], coords[1:], coords[2:])
            if numpy.cross(nextCoord - prevCoord, coord - prevCoord) != 0
        ])
        collapsedCoords.append(coords[-1])
        collapsedCoords = numpy.array(collapsedCoords)
        return collapsedCoords

    @classmethod
    def maskToContour(cls, maskImage: numpy.ndarray) -> numpy.ndarray:
        """
        Extract the contour line within a segmented label mask, using Scikit-Image.

        :param maskImage: A binary label mask of numpy.uint8.
        :return: An array of point pairs.
        """
        if maskImage.dtype != numpy.uint8:
            raise TypeError('maskImage must be an array of uint8.')

        coords = skimage.measure.find_contours(
            # TODO: threshold image more efficiently
            array=maskImage.astype(bool).astype(numpy.double),
            level=0.5,
            fully_connected='low',
            positive_orientation='low'
        )
        coords = numpy.fliplr(coords[0])
        coords = cls._collapseCoords(coords)
        return coords

    @classmethod
    def contourToMask(cls, imageShape: Tuple[int, int], coords: numpy.ndarray) -> numpy.ndarray:
        """
        Convert a contour line to a label mask.

        :param imageShape: The [Y, X] shape of the image.
        :param coords: An array of point pairs.
        :return: A binary label mask of numpy.uint8.
        """
        maskImage = skimage.measure.grid_points_in_poly(
            shape=imageShape,
            verts=numpy.fliplr(coords)
        ).astype(numpy.uint8)
        maskImage *= 255
        return maskImage

    @classmethod
    def _slic(cls, image, numSegments=None, segmentSize=None):
        compactness = 0.01  # make superpixels highly deformable
        maxIter = 10
        sigma = 2.0

        if numSegments and segmentSize:
            raise ValueError(
                'Only one of numSegments or segmentSize may be set.')
        elif numSegments:
            pass
        elif segmentSize:
            numSegments = (image.shape[0] * image.shape[1]) / (segmentSize ** 2)
        else:
            raise ValueError('One of numSegments or segmentSize must be set.')

        labelImage = skimage.segmentation.slic(
            image,
            n_segments=numSegments,
            compactness=compactness,
            max_iter=maxIter,
            sigma=sigma,
            enforce_connectivity=True,
            min_size_factor=0.5,
            slic_zero=True
        )
        return labelImage

    class _PersistentCounter(object):
        def __init__(self):
            self.value = 0

        def __call__(self):
            ret = self.value
            self.value += 1
            return ret

    @classmethod
    def _uint64ToRGB(cls, val):
        return numpy.dstack((
            val.astype(numpy.uint8),
            (val >> numpy.uint64(8)).astype(numpy.uint8),
            (val >> numpy.uint64(16)).astype(numpy.uint8)
        ))

    @classmethod
    def _RGBTounit64(cls, val: numpy.ndarray) -> numpy.ndarray:
        """
        Decode an RGB representation of a superpixel label into its native scalar value.

        :param val: A single pixel, or a 3-channel image.
                    This is an numpy.ndarray of uint8, with a shape [3] or [n, m, 3].
        """
        return \
            (val[..., 0].astype(numpy.uint64)) + \
            (val[..., 1].astype(numpy.uint64) << numpy.uint64(8)) + \
            (val[..., 2].astype(numpy.uint64) << numpy.uint64(16))

    @classmethod
    def superpixels(cls, image):
        superpixelLabels = cls._slic(image, numSegments=1000)
        superpixels = cls._uint64ToRGB(superpixelLabels)
        return superpixels

    @classmethod
    def superpixels_legacy(cls, image, coords):
        maskImage = cls.contourToMask(image.shape[:2], coords)

        from .opencv import OpenCVSegmentationHelper
        # This operation is much faster in OpenCV
        maskImage = OpenCVSegmentationHelper._binaryOpening(
            maskImage.astype(numpy.uint8),
            elementShape='circle',
            elementRadius=5
        ).astype(bool)

        insideImage = image.copy()
        insideImage[numpy.logical_not(maskImage)] = 0
        insideSuperpixelLabels = cls._slic(insideImage, segmentSize=20)

        outsideImage = image.copy()
        outsideImage[maskImage] = 0
        outsideSuperpixelLabels = cls._slic(outsideImage, segmentSize=60)

        # https://stackoverflow.com/questions/16210738/implementation-of-numpy-in1d-for-2d-arrays
        insideSuperpixelMask = numpy.in1d(
            insideSuperpixelLabels.flat,
            numpy.unique(insideSuperpixelLabels[maskImage])
        ).reshape(insideSuperpixelLabels.shape)

        combinedSuperpixelLabels = outsideSuperpixelLabels.copy()
        combinedSuperpixelLabels[insideSuperpixelMask] = \
            insideSuperpixelLabels[insideSuperpixelMask] + \
            outsideSuperpixelLabels.max() + 10000

        labelValues = collections.defaultdict(cls._PersistentCounter())
        for value in numpy.nditer(combinedSuperpixelLabels,
                                  op_flags=['readwrite']):
            value[...] = labelValues[value.item()]

        combinedSuperpixels = cls._uint64ToRGB(combinedSuperpixelLabels)
        return combinedSuperpixels
