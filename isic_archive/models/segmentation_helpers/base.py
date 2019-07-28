from io import BytesIO
from typing import BinaryIO, Union

import numpy


class BaseSegmentationHelper(object):
    @classmethod
    def loadImage(cls, imageDataStream: Union[BinaryIO, BytesIO]) -> numpy.ndarray:
        """
        Load an image into an RGB array.

        :param imageDataStream: A file-like object containing the encoded
        (JPEG, etc.) image data.
        :return: A Numpy array with the RGB image data.
        """
        raise NotImplementedError()

    @classmethod
    def writeImage(cls, image, encoding='png'):
        # TODO: cv2.imencode
        raise NotImplementedError()

    @classmethod
    def segment(cls, image, seedCoord, tolerance):
        raise NotImplementedError()
