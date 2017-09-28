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
import six
import sys

from tests import base


class DatasetHelpersTestCase(base.TestCase):
    def setUp(self):
        # A Girder instance is not required for this test case

        # Load function under test
        isicModelsModulePath = os.path.abspath(os.path.join(
            os.path.dirname(__file__), '..', 'server', 'models'))
        if isicModelsModulePath not in sys.path:
            sys.path.append(isicModelsModulePath)

        from dataset_helpers import matchFilenameRegex
        self.matchFilenameRegex = matchFilenameRegex

    def assertMatch(self, originalFilename, csvFilename):
        """Assert that the filename in the CSV matches the original filename."""
        regex = self.matchFilenameRegex(csvFilename)
        six.assertRegex(self, originalFilename, regex)

    def assertNotMatch(self, originalFilename, csvFilename):
        """Assert that the filename in the CSV doesn't match the original filename."""
        regex = self.matchFilenameRegex(csvFilename)
        self.assertNotRegexpMatches(originalFilename, regex)

    def testMatchFilenameRegex(self):
        """
        Test the function that generates a regular expression to match image
        filenames in a metadata CSV file to original image filenames in the
        database.
        """
        originalFilename = 'ABC-6D.JPG'
        self.assertMatch(originalFilename, 'ABC-6D')
        self.assertMatch(originalFilename, 'ABC-6D.JPG')
        self.assertMatch(originalFilename, 'ABC-6D.jpg')
        self.assertMatch(originalFilename, 'abc-6D.jpg')
        self.assertMatch(originalFilename, 'abc-6d.jpg')
        self.assertNotMatch(originalFilename, 'ABC-6D.png')
        self.assertNotMatch(originalFilename, 'ABC-6D.PNG')

        originalFilename = '20010425124238356.jpg'
        self.assertMatch(originalFilename, '20010425124238356')
        self.assertMatch(originalFilename, '20010425124238356.jpg')
        self.assertMatch(originalFilename, '20010425124238356.JPG')
        self.assertNotMatch(originalFilename, '20010425124238356.png')
        self.assertNotMatch(originalFilename, '20010425124238356.PNG')

        originalFilename = 'AbcDef00598.jpg'
        self.assertMatch(originalFilename, 'AbcDef00598')
        self.assertMatch(originalFilename, 'AbcDef00598.jpg')
        self.assertMatch(originalFilename, 'AbcDef00598.JPG')
        self.assertMatch(originalFilename, 'abcdef00598.JPG')
        self.assertNotMatch(originalFilename, 'AbcDef00598.png')
        self.assertNotMatch(originalFilename, 'AbcDef00598.PNG')

        originalFilename = 'test-20010425124238356.jpg'
        self.assertMatch(originalFilename, 'test-20010425124238356')
        self.assertMatch(originalFilename, 'test-20010425124238356.jpg')
        self.assertMatch(originalFilename, 'TEST-20010425124238356.jpg')
        self.assertMatch(originalFilename, 'TEST-20010425124238356.JPG')
        self.assertNotMatch(originalFilename, 'TEST-20010425124238356.png')
        self.assertNotMatch(originalFilename, 'TEST-20010425124238356.PNG')

        originalFilename = 'AEOU3014, (20020901020318037) 20010425124238356.jpg'
        self.assertMatch(originalFilename, 'AEOU3014, (20020901020318037) 20010425124238356')
        self.assertMatch(originalFilename, 'AEOU3014, (20020901020318037) 20010425124238356.jpg')
        self.assertMatch(originalFilename, 'AEOU3014, (20020901020318037) 20010425124238356.JPG')
        self.assertMatch(originalFilename, 'aeou3014, (20020901020318037) 20010425124238356.JPG')
        self.assertMatch(originalFilename, 'aeou3014, (20020901020318037) 20010425124238356.jpg')
        self.assertNotMatch(originalFilename, 'AEOU3014, (20020901020318037) 20010425124238356.png')
        self.assertNotMatch(originalFilename, 'AEOU3014, (20020901020318037) 20010425124238356.PNG')

        originalFilename = '20020901020318037_30445187_2002-0901_Null_ 001.jpg'
        self.assertMatch(originalFilename, '20020901020318037_30445187_2002-0901_Null_ 001')
        self.assertMatch(originalFilename, '20020901020318037_30445187_2002-0901_Null_ 001.jpg')
        self.assertMatch(originalFilename, '20020901020318037_30445187_2002-0901_Null_ 001.JPG')
        self.assertMatch(originalFilename, '20020901020318037_30445187_2002-0901_NULL_ 001.jpg')
        self.assertMatch(originalFilename, '20020901020318037_30445187_2002-0901_NULL_ 001.JPG')
        self.assertNotMatch(originalFilename, '20020901020318037_30445187_2002-0901_NULL_ 001.png')
        self.assertNotMatch(originalFilename, '20020901020318037_30445187_2002-0901_NULL_ 001.PNG')

        # Filename that contains a period
        originalFilename = 'test.315704d.jpg'
        self.assertMatch(originalFilename, 'test.315704d')
        self.assertMatch(originalFilename, 'test.315704d.jpg')
        self.assertNotMatch(originalFilename, 'test.315704d.PNG')

        # Filename that contains multiple periods
        originalFilename = 'test.315704d.4e95e3d.png'
        self.assertMatch(originalFilename, 'test.315704d.4e95e3d')
        self.assertMatch(originalFilename, 'test.315704d.4e95e3d.png')
        self.assertNotMatch(originalFilename, 'test.315704d')
        self.assertNotMatch(originalFilename, 'test.315704d.4e95e3d.')
        self.assertNotMatch(originalFilename, 'test.315704d.4e95e3d.jpg')
