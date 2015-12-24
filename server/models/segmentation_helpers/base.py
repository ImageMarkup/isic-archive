#!/usr/bin/env python
# -*- coding: utf-8 -*-


class BaseSegmentationHelper(object):
    @classmethod
    def loadImage(cls, image_data_stream):
        """
        Load an image into an RGB array.
        :param image_data_stream: A file-like object containing the encoded
        (JPEG, etc.) image data.
        :type image_data_stream: file-like object
        :return: An Numpy array with the RGB image data.
        :rtype: numpy.ndarray
        """
        raise NotImplementedError()

    @classmethod
    def segment(cls, image, seed_coord, tolerance):
        raise NotImplementedError()
