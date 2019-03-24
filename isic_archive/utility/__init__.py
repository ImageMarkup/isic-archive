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


def generateLines(stream):
    """
    Generate individual unicode lines of text from a stream.

    Newlines are retained in the output. Decoding using 'utf-8-sig' removes Unicode BOM
    (byte order mark).
    """
    lastLine = None
    keepends = True
    try:
        # Read chunk from stream and split into lines. Always process the
        # last line with the next chunk, or at the end of the stream,
        # because it may be incomplete.
        while True:
            chunk = ''.join(next(stream))
            if lastLine is not None:
                chunk = lastLine + chunk
            lines = chunk.splitlines(keepends)
            lastLine = lines.pop()
            for line in lines:
                yield line
    except StopIteration:
        if lastLine is not None:
            yield lastLine
        raise StopIteration
