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

import os
import re


def matchFilenameRegex(filename):
    """
    Generate a regex to match image filenames in a metadata CSV file to original image filenames.

    The filenames in the CSV may or may not include file extensions. When the
    filename does include an extension, it must match the extension of the
    original filename. The extension must be in the list of valid extensions.

    The comparison ignores case.

    :param filename: The image filename in the CSV file.
    :return: The regular expression.
    """
    # Split filename into root and extension.
    # If the extension is not empty, it begins with a period.
    root, extension = os.path.splitext(filename)

    # If the detected extension isn't recognized, assume it's part of the
    # filename. This allows filenames to contain periods.
    validExtensions = ['bmp', 'jpeg', 'jpg', 'png', 'tif', 'tiff']
    if extension and extension.lower()[1:] not in validExtensions:
        root += extension
        extension = ''

    # Escape special characters in filename components
    root = re.escape(root)
    extension = re.escape(extension)

    # When no extension is provided, match any extension
    if not extension:
        extension = r'\.\w+'

    # Compile regular expression
    pattern = '^%s%s$' % (root, extension)
    regex = re.compile(pattern, re.IGNORECASE)

    return regex
