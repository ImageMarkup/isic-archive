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
