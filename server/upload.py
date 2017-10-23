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
import sys
import subprocess
import tempfile
import zipfile

from girder.utility import assetstore_utilities
from girder.utility.model_importer import ModelImporter


class TempDir(object):
    def __init__(self):
        pass

    def __enter__(self):
        Assetstore = ModelImporter.model('assetstore')
        assetstore = Assetstore.getCurrent()
        assetstoreAdapter = assetstore_utilities.getAssetstoreAdapter(
            assetstore)
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
        try:
            return self._defaultUnzip()
        except (zipfile.BadZipfile, NotImplementedError):
            return self._fallbackUnzip()

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

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
        with TempDir() as temp_dir:
            for originalFile, originalFileRelpath in fileList:
                originalFileName = os.path.basename(originalFileRelpath)
                tempFilePath = os.path.join(temp_dir, originalFileName)
                with open(tempFilePath, 'wb') as tempFileStream:
                    shutil.copyfileobj(
                        zipFile.open(originalFile),
                        tempFileStream
                    )
                yield tempFilePath, originalFileRelpath
                os.remove(tempFilePath)
            zipFile.close()

    def _fallbackUnzip(self):
        with TempDir() as tempDir:
            unzipCommand = (
                '7z',
                'x',
                '-y',
                '-o%s' % tempDir,
                self.zipFilePath
            )
            try:
                with open(os.devnull, 'rb') as nullIn,\
                        open(os.devnull, 'wb') as nullOut:
                    subprocess.check_call(
                        unzipCommand, stdin=nullIn, stdout=nullOut,
                        stderr=subprocess.STDOUT)
            except subprocess.CalledProcessError:
                self.__exit__(*sys.exc_info())
                raise

            fileList = []
            for tempDirPath, _, tempFileNames in os.walk(tempDir):
                for tempFileName in tempFileNames:
                    tempFilePath = os.path.join(tempDirPath, tempFileName)
                    originalFileRelpath = os.path.relpath(
                        tempFilePath, tempDir)
                    if tempFileName.startswith('._'):
                        # file is probably a macOS resource fork, skip
                        continue
                    fileList.append((tempFilePath, originalFileRelpath))
            return iter(fileList), len(fileList)
