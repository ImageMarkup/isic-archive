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
import sys

from six.moves import range
from tests import base


class DataIterator(object):
    """
    For testing, an iterator that returns data in chunks of the specified size.
    """
    def __init__(self, data, chunkSize):
        self.data = data
        self.chunkSize = chunkSize
        self.pos = 0
        self.dataLen = len(self.data)

    def __iter__(self):
        return self

    def __next__(self):
        if self.pos >= self.dataLen:
            raise StopIteration
        nextPos = self.pos + self.chunkSize
        curData = self.data[self.pos:nextPos]
        self.pos = nextPos
        return curData

    # Support Python 2 iterator method name
    next = __next__


def setUpModule():
    isicUtilityModulePath = os.path.abspath(os.path.join(
        os.path.dirname(__file__), '..', 'server'))
    if isicUtilityModulePath not in sys.path:
        sys.path.append(isicUtilityModulePath)

    global generateLines
    from utility import generateLines


class UtilityTestCase(base.TestCase):
    def setUp(self):
        # A Girder instance is not required for this test case
        pass

    def testGenerateLines(self):
        """
        Test generateLines with all chunk sizes up to a maximum larger than the
        longest input data. To control the chunk size we use the helper class
        DataIterator in place of something like StringIO. Testing with chunk
        sizes smaller than the data size is necessary to effective test the
        implementation of generateLines.
        """
        for chunkSize in range(1, 21):
            self._testGenerateLines(chunkSize)

    def _generateLines(self, data, chunkSize):
        """
        Helper method to return the result of generateLines() on input data
        retrieved from an iterator that uses specified chunk size.
        """
        return generateLines(DataIterator(data, chunkSize))

    def _testGenerateLines(self, chunkSize):
        """Run all generateLines tests for the specified chunk size."""
        self._testGenerateLinesEmpty(chunkSize)
        self._testGenerateLinesSingleLine(chunkSize)
        self._testGenerateLinesMultipleLines(chunkSize)
        self._testGenerateLinesBlankLines(chunkSize)

    def _testGenerateLinesEmpty(self, chunkSize):
        """Test generateLines on empty input."""
        # With newline at end
        lines = self._generateLines('\n', chunkSize)
        line = lines.next()
        self.assertEqual(len(line), 1)
        with self.assertRaises(StopIteration):
            lines.next()

        # Without newline at end
        lines = self._generateLines('', chunkSize)
        with self.assertRaises(StopIteration):
            lines.next()

    def _testGenerateLinesSingleLine(self, chunkSize):
        """Test generateLines on input with a single line."""
        # With newline at end
        lines = self._generateLines('abc\n', chunkSize)
        line = lines.next()
        self.assertEqual(len(line), 4)
        with self.assertRaises(StopIteration):
            lines.next()

        # Without newline at end
        lines = self._generateLines('abc', chunkSize)
        line = lines.next()
        self.assertEqual(len(line), 3)
        with self.assertRaises(StopIteration):
            lines.next()

    def _testGenerateLinesMultipleLines(self, chunkSize):
        """Test generateLines on input with multiple lines."""
        lines = self._generateLines('abc\ndef\n', chunkSize)
        line = lines.next()
        self.assertEqual(len(line), 4)
        line = lines.next()
        self.assertEqual(len(line), 4)
        with self.assertRaises(StopIteration):
            lines.next()

        lines = self._generateLines('abc\ndef\nhijklmnop\n', chunkSize)
        line = lines.next()
        self.assertEqual(len(line), 4)
        line = lines.next()
        self.assertEqual(len(line), 4)
        line = lines.next()
        self.assertEqual(len(line), 10)
        with self.assertRaises(StopIteration):
            lines.next()

    def _testGenerateLinesBlankLines(self, chunkSize):
        """Test generateLines on input that contains blank lines."""
        lines = self._generateLines('abc\n\n', chunkSize)
        line = lines.next()
        self.assertEqual(len(line), 4)
        line = lines.next()
        self.assertEqual(len(line), 1)
        with self.assertRaises(StopIteration):
            lines.next()

        lines = self._generateLines('\nabc\n', chunkSize)
        line = lines.next()
        self.assertEqual(len(line), 1)
        line = lines.next()
        self.assertEqual(len(line), 4)
        with self.assertRaises(StopIteration):
            lines.next()
