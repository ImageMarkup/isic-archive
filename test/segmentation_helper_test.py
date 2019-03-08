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
import numpy

from isic_archive.models.segmentation_helpers import OpenCVSegmentationHelper, \
    ScikitSegmentationHelper

testImage = numpy.array([
    [128, 128, 0, 0, 0, 0],
    [128, 128, 128, 128, 0, 0],
    [0, 128, 0, 128, 128, 128],
    [0, 128, 128, 128, 0, 0],
    [0, 0, 128, 0, 0, 128],
    [0, 0, 0, 128, 0, 128]
], dtype=numpy.uint8)

# Will be used to make sure functions don't mutate inputs
originalTestImage = testImage.copy()


def testOpenCVSegmentationHelper():
    _testFloodFill(OpenCVSegmentationHelper)
    _testSegment(OpenCVSegmentationHelper)

    _testEasyMaskToContour(OpenCVSegmentationHelper)
    _testHardMaskToContour(OpenCVSegmentationHelper)


def testScikitSegmentationHelper():
    _testFloodFill(ScikitSegmentationHelper)
    _testSegment(ScikitSegmentationHelper)

    # Test _clippedAdd
    testImage = numpy.array([2, 128, 253], numpy.uint8)
    originalTestImage = testImage.copy()
    assert numpy.array_equal(
        ScikitSegmentationHelper._clippedAdd(testImage, 5),
        numpy.array([7, 133, 255], numpy.uint8))
    assert numpy.array_equal(testImage, originalTestImage)
    assert numpy.array_equal(
        ScikitSegmentationHelper._clippedAdd(testImage, -5),
        numpy.array([0, 123, 248], numpy.uint8))
    assert numpy.array_equal(testImage, originalTestImage)

    _testEasyMaskToContour(ScikitSegmentationHelper)
    # TODO: this is broken, likely due to coordinate rounding issues
    # _testHardMaskToContour(ScikitSegmentationHelper)


def _testFloodFill(SegmentationHelper):
    filledMask = SegmentationHelper._floodFill(
        testImage, (1, 1), 5, connectivity=8)
    assert numpy.array_equal(
        filledMask,
        numpy.array([
            [255, 255, 0, 0, 0, 0],
            [255, 255, 255, 255, 0, 0],
            [0, 255, 0, 255, 255, 255],
            [0, 255, 255, 255, 0, 0],
            [0, 0, 255, 0, 0, 0],
            [0, 0, 0, 255, 0, 0]
        ], dtype=numpy.uint8))
    assert numpy.array_equal(testImage, originalTestImage)

    # Now, with connectivity=4
    filledMask = SegmentationHelper._floodFill(
        testImage, (1, 1), 5, connectivity=4)
    assert numpy.array_equal(
        filledMask,
        numpy.array([
            [255, 255, 0, 0, 0, 0],
            [255, 255, 255, 255, 0, 0],
            [0, 255, 0, 255, 255, 255],
            [0, 255, 255, 255, 0, 0],
            [0, 0, 255, 0, 0, 0],
            [0, 0, 0, 0, 0, 0]
        ], dtype=numpy.uint8))
    assert numpy.array_equal(testImage, originalTestImage)

    # TODO: Test RGB images, particularly with SciKit


def _testSegment(SegmentationHelper):
    segmentedMask = SegmentationHelper.segment(
        testImage, (1, 1), 5)
    assert numpy.array_equal(
        segmentedMask,
        numpy.array([
            [255, 255, 0, 0, 0, 0],
            [255, 255, 255, 255, 0, 0],
            [0, 255, 255, 255, 255, 255],
            [0, 255, 255, 255, 0, 0],
            [0, 0, 255, 0, 0, 0],
            [0, 0, 0, 255, 0, 0]
        ], dtype=numpy.uint8))
    assert numpy.array_equal(testImage, originalTestImage)

    # TODO: test tolerance more thoroughly


def _testMaskToContour(SegmentationHelper, inputMask):
    originalInputMask = inputMask.copy()

    contour = SegmentationHelper.maskToContour(inputMask)
    assert isinstance(contour, numpy.ndarray)
    assert len(contour.shape) == 2
    assert contour.shape[1] == 2
    assert numpy.array_equal(inputMask, originalInputMask)

    originalContour = contour.copy()
    outputMask = SegmentationHelper.contourToMask(inputMask.shape, contour)
    assert isinstance(outputMask, numpy.ndarray)
    assert outputMask.shape == inputMask.shape
    assert outputMask.dtype == numpy.uint8
    assert numpy.array_equal(outputMask, inputMask)
    assert numpy.array_equal(contour, originalContour)


def _testEasyMaskToContour(SegmentationHelper):
    inputMask = numpy.zeros((20, 20), dtype=numpy.uint8)
    inputMask[5:15, 5:15] = 255
    _testMaskToContour(SegmentationHelper, inputMask)


def _testHardMaskToContour(SegmentationHelper):
    inputMask = SegmentationHelper.segment(
        testImage, (1, 1), 5)
    _testMaskToContour(SegmentationHelper, inputMask)
