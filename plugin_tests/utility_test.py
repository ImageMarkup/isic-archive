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

from six.moves import range

import pytest

from isic_archive.utility import generateLines


class DataIterator(object):
    """For testing, an iterator that returns data in chunks of the specified size."""

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


def testGenerateLines():
    """
    Test generateLines with all chunk sizes up to a maximum larger than the longest input data.

    To control the chunk size we use the helper class
    DataIterator in place of something like StringIO. Testing with chunk
    sizes smaller than the data size is necessary to effective test the
    implementation of generateLines.
    """
    for chunkSize in range(1, 21):
        _testGenerateLines(chunkSize)

def _generateLines(data, chunkSize):
    """Return generateLines() on input data retrieved with a specified chunk size."""
    return generateLines(DataIterator(data, chunkSize))

def _testGenerateLines(chunkSize):
    """Run all generateLines tests for the specified chunk size."""
    _testGenerateLinesEmpty(chunkSize)
    _testGenerateLinesSingleLine(chunkSize)
    _testGenerateLinesMultipleLines(chunkSize)
    _testGenerateLinesBlankLines(chunkSize)

def _testGenerateLinesEmpty(chunkSize):
    """Test generateLines on empty input."""
    # With newline at end
    lines = _generateLines('\n', chunkSize)
    line = lines.next()
    assert len(line) == 1
    with pytest.raises(StopIteration):
        lines.next()

    # Without newline at end
    lines = _generateLines('', chunkSize)
    with pytest.raises(StopIteration):
        lines.next()

def _testGenerateLinesSingleLine(chunkSize):
    """Test generateLines on input with a single line."""
    # With newline at end
    lines = _generateLines('abc\n', chunkSize)
    line = lines.next()
    assert len(line) == 4
    with pytest.raises(StopIteration):
        lines.next()

    # Without newline at end
    lines = _generateLines('abc', chunkSize)
    line = lines.next()
    assert len(line) == 3
    with pytest.raises(StopIteration):
        lines.next()

def _testGenerateLinesMultipleLines(chunkSize):
    """Test generateLines on input with multiple lines."""
    lines = _generateLines('abc\ndef\n', chunkSize)
    line = lines.next()
    assert len(line) == 4
    line = lines.next()
    assert len(line) == 4
    with pytest.raises(StopIteration):
        lines.next()

    lines = _generateLines('abc\ndef\nhijklmnop\n', chunkSize)
    line = lines.next()
    assert len(line) == 4
    line = lines.next()
    assert len(line) == 4
    line = lines.next()
    assert len(line) == 10
    with pytest.raises(StopIteration):
        lines.next()

def _testGenerateLinesBlankLines(chunkSize):
    """Test generateLines on input that contains blank lines."""
    lines = _generateLines('abc\n\n', chunkSize)
    line = lines.next()
    assert len(line) == 4
    line = lines.next()
    assert len(line) == 1
    with pytest.raises(StopIteration):
        lines.next()

    lines = _generateLines('\nabc\n', chunkSize)
    line = lines.next()
    assert len(line) == 1
    line = lines.next()
    assert len(line) == 4
    with pytest.raises(StopIteration):
        lines.next()
