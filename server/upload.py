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
import shutil
import subprocess
import sys
import tempfile
import zipfile

from girder.models.assetstore import Assetstore
from girder.utility import assetstore_utilities


class TempDir(object):
    def __init__(self):
        pass

    def __enter__(self):
        assetstore = Assetstore().getCurrent()
        assetstoreAdapter = assetstore_utilities.getAssetstoreAdapter(assetstore)
        try:
            self.tempDir = tempfile.mkdtemp(dir=assetstoreAdapter.tempDir)
        except (AttributeError, OSError):
            self.tempDir = tempfile.mkdtemp()
        return self.tempDir

    def __exit__(self, exc_type, exc_val, exc_tb):
        shutil.rmtree(self.tempDir)


class ZipFileOpener(object):
    def __init__(self, zip_file_path):
        self.zipFilePath = zip_file_path
        # TODO: check for "7z" command

    def __enter__(self):
        # Create temporary directory
        self.tempDirManager = TempDir()
        self.tempDir = self.tempDirManager.__enter__()

        try:
            return self._defaultUnzip()
        except (zipfile.BadZipfile, NotImplementedError):
            return self._fallbackUnzip()

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Destroy temporary directory
        self.tempDirManager.__exit__(exc_type, exc_val, exc_tb)

    def _defaultUnzip(self):
        zipFile = zipfile.ZipFile(self.zipFilePath)

        # filter out directories and count real files
        fileList = []
        for originalFile in zipFile.infolist():
            originalFileRelpath = originalFile.filename
            originalFileRelpath.replace('\\', '/')
            originalFileName = os.path.basename(originalFileRelpath)
            if not originalFileName or not originalFile.file_size:
                # file is probably a directory, skip
                continue
            if originalFileName.startswith('._'):
                # file is probably a macOS resource fork, skip
                continue
            fileList.append((originalFile, originalFileRelpath))
        # Test whether the archive uses a compression type that the zipfile module supports. For
        # example, extracting from an archive that uses Deflate64 raises the following exception:
        # "NotImplementedError: compression type 9 (deflate64)"
        if fileList:
            with zipFile.open(fileList[0][0]):
                pass

        return self._defaultUnzipIter(zipFile, fileList), len(fileList)

    def _defaultUnzipIter(self, zipFile, fileList):
        for originalFile, originalFileRelpath in fileList:
            originalFileName = os.path.basename(originalFileRelpath)
            tempFilePath = os.path.join(self.tempDir, originalFileName)
            with open(tempFilePath, 'wb') as tempFileStream:
                shutil.copyfileobj(zipFile.open(originalFile), tempFileStream)
            yield tempFilePath, originalFileRelpath
            os.remove(tempFilePath)
        zipFile.close()

    def _fallbackUnzip(self):
        unzipCommand = ('7z', 'x', '-y', '-o%s' % self.tempDir, self.zipFilePath)
        try:
            with open(os.devnull, 'rb') as nullIn, open(os.devnull, 'wb') as nullOut:
                subprocess.check_call(
                    unzipCommand, stdin=nullIn, stdout=nullOut, stderr=subprocess.STDOUT
                )
        except subprocess.CalledProcessError:
            self.__exit__(*sys.exc_info())
            raise

        fileList = []
        for tempDirPath, _, tempFileNames in os.walk(self.tempDir):
            for tempFileName in tempFileNames:
                tempFilePath = os.path.join(tempDirPath, tempFileName)
                originalFileRelpath = os.path.relpath(tempFilePath, self.tempDir)
                if tempFileName.startswith('._'):
                    # file is probably a macOS resource fork, skip
                    continue
                fileList.append((tempFilePath, originalFileRelpath))
        return iter(fileList), len(fileList)
