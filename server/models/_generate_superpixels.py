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

import os
import sys

# Worker-defined inputs
originalFile = globals()['originalFile']
segmentation_helpersPath = globals()['segmentation_helpersPath']

segmentation_helpersDirPath = os.path.dirname(segmentation_helpersPath)
if segmentation_helpersDirPath not in sys.path:
    sys.path.append(segmentation_helpersDirPath)
from segmentation_helpers.scikit import ScikitSegmentationHelper  # noqa


with open(originalFile, 'rb') as originalFileStream:
    # Scikit-Image is ~70ms faster at decoding image data
    originalImageData = ScikitSegmentationHelper.loadImage(originalFileStream)

superpixelsData = ScikitSegmentationHelper.superpixels(originalImageData)
superpixelsEncodedStream = ScikitSegmentationHelper.writeImage(
    superpixelsData, 'png')

superpixelsEncodedBytes = superpixelsEncodedStream.getvalue()
