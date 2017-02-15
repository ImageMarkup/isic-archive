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

import sys
import os

import numpy

from tests import base

OpenCVSegmentationHelper = None
ScikitSegmentationHelper = None


def setUpModule():
    isicModelsModulePath = os.path.abspath(os.path.join(
        os.path.dirname(__file__), '..', 'server', 'models'))
    if isicModelsModulePath not in sys.path:
        sys.path.append(isicModelsModulePath)

    global OpenCVSegmentationHelper, ScikitSegmentationHelper
    from segmentation_helpers import OpenCVSegmentationHelper, \
        ScikitSegmentationHelper


class SegmentationHelperTestCase(base.TestCase):
    def setUp(self):
        # A Girder instance is not required for this test case

        self.testImage = numpy.array([
            [128, 128, 0, 0, 0, 0],
            [128, 128, 128, 128, 0, 0],
            [0, 128, 0, 128, 128, 128],
            [0, 128, 128, 128, 0, 0],
            [0, 0, 128, 0, 0, 128],
            [0, 0, 0, 128, 0, 128]
        ], dtype=numpy.uint8)

        # Will be used to make sure functions don't mutate inputs
        self.originalTestImage = self.testImage.copy()

    def assertArrayEqual(self, first, second):
        """Fail if the two NumPy arrays are unequal."""
        self.assertTrue(
            numpy.array_equal(first, second),
            'NumPy arrays \n'
            '%s\n'
            'and\n'
            '%s\n '
            'are not equal' % (first, second))

    def testOpenCVSegmentationHelper(self):
        self._testFloodFill(OpenCVSegmentationHelper)
        self._testSegment(OpenCVSegmentationHelper)

        self._testEasyMaskToContour(OpenCVSegmentationHelper)
        self._testHardMaskToContour(OpenCVSegmentationHelper)

    def testScikitSegmentationHelper(self):
        self._testFloodFill(ScikitSegmentationHelper)
        self._testSegment(ScikitSegmentationHelper)

        # Test _clippedAdd
        testImage = numpy.array([2, 128, 253], numpy.uint8)
        originalTestImage = testImage.copy()
        self.assertArrayEqual(
            ScikitSegmentationHelper._clippedAdd(testImage, 5),
            numpy.array([7, 133, 255], numpy.uint8))
        self.assertArrayEqual(testImage, originalTestImage)
        self.assertArrayEqual(
            ScikitSegmentationHelper._clippedAdd(testImage, -5),
            numpy.array([0, 123, 248], numpy.uint8))
        self.assertArrayEqual(testImage, originalTestImage)

        self._testEasyMaskToContour(ScikitSegmentationHelper)
        # TODO: this is broken, likely due to coordinate rounding issues
        # self._testHardMaskToContour(ScikitSegmentationHelper)

    def _testFloodFill(self, SegmentationHelper):
        filledMask = SegmentationHelper._floodFill(
            self.testImage, (1, 1), 5, connectivity=8)
        self.assertArrayEqual(
            filledMask,
            numpy.array([
                [255, 255, 0, 0, 0, 0],
                [255, 255, 255, 255, 0, 0],
                [0, 255, 0, 255, 255, 255],
                [0, 255, 255, 255, 0, 0],
                [0, 0, 255, 0, 0, 0],
                [0, 0, 0, 255, 0, 0]
            ], dtype=numpy.uint8))
        self.assertArrayEqual(self.testImage, self.originalTestImage)

        # Now, with connectivity=4
        filledMask = SegmentationHelper._floodFill(
            self.testImage, (1, 1), 5, connectivity=4)
        self.assertArrayEqual(
            filledMask,
            numpy.array([
                [255, 255, 0, 0, 0, 0],
                [255, 255, 255, 255, 0, 0],
                [0, 255, 0, 255, 255, 255],
                [0, 255, 255, 255, 0, 0],
                [0, 0, 255, 0, 0, 0],
                [0, 0, 0, 0, 0, 0]
            ], dtype=numpy.uint8))
        self.assertArrayEqual(self.testImage, self.originalTestImage)

        # TODO: Test RGB images, particularly with SciKit

    def _testSegment(self, SegmentationHelper):
        segmentedMask = SegmentationHelper.segment(
            self.testImage, (1, 1), 5)
        self.assertArrayEqual(
            segmentedMask,
            numpy.array([
                [255, 255, 0, 0, 0, 0],
                [255, 255, 255, 255, 0, 0],
                [0, 255, 255, 255, 255, 255],
                [0, 255, 255, 255, 0, 0],
                [0, 0, 255, 0, 0, 0],
                [0, 0, 0, 255, 0, 0]
            ], dtype=numpy.uint8))
        self.assertArrayEqual(self.testImage, self.originalTestImage)

        # TODO: test tolerance more thoroughly

    def _testMaskToContour(self, SegmentationHelper, inputMask):
        originalInputMask = inputMask.copy()

        contour = SegmentationHelper.maskToContour(inputMask)
        self.assertIsInstance(contour, numpy.ndarray)
        self.assertEqual(len(contour.shape), 2)
        self.assertEqual(contour.shape[1], 2)
        self.assertArrayEqual(inputMask, originalInputMask)

        originalContour = contour.copy()
        outputMask = SegmentationHelper.contourToMask(inputMask.shape, contour)
        self.assertIsInstance(outputMask, numpy.ndarray)
        self.assertEqual(outputMask.shape, inputMask.shape)
        self.assertEqual(outputMask.dtype, numpy.uint8)
        self.assertArrayEqual(outputMask, inputMask)
        self.assertArrayEqual(contour, originalContour)

    def _testEasyMaskToContour(self, SegmentationHelper):
        inputMask = numpy.zeros((20, 20), dtype=numpy.uint8)
        inputMask[5:15, 5:15] = 255
        self._testMaskToContour(SegmentationHelper, inputMask)

    def _testHardMaskToContour(self, SegmentationHelper):
        inputMask = SegmentationHelper.segment(
            self.testImage, (1, 1), 5)
        self._testMaskToContour(SegmentationHelper, inputMask)
