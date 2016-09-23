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

import csv
import os
import shutil
import sys
import subprocess
import tempfile
import zipfile

from girder.models.model_base import ValidationException
from girder.models.notification import ProgressState
from girder.utility import assetstore_utilities
from girder.utility.model_importer import ModelImporter
from girder.utility.progress import ProgressContext

from .provision_utility import getAdminUser


class TempDir(object):
    def __init__(self):
        pass

    def __enter__(self):
        assetstore = ModelImporter.model('assetstore').getCurrent()
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
        except zipfile.BadZipfile:
            return self._fallbackUnzip()

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def _defaultUnzip(self):
        zipFile = zipfile.ZipFile(self.zipFilePath)

        # filter out directories and count real files
        fileList = list()
        for originalFile in zipFile.infolist():
            originalFileRelpath = originalFile.filename
            originalFileRelpath.replace('\\', '/')
            originalFileName = os.path.basename(originalFileRelpath)
            if not originalFileName or not originalFile.file_size:
                # file is probably a directory, skip
                continue
            fileList.append((originalFile, originalFileRelpath))
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

            fileList = list()
            for tempDirPath, _, tempFileNames in os.walk(tempDir):
                for tempFileName in tempFileNames:
                    tempFilePath = os.path.join(tempDirPath, tempFileName)
                    originalFileRelpath = os.path.relpath(
                        tempFilePath, tempDir)
                    fileList.append((tempFilePath, originalFileRelpath))
            return iter(fileList), len(fileList)


def handleZip(imagesFolder, user, zipFile):
    Image = ModelImporter.model('image', 'isic_archive')

    # Get full path of zip file in assetstore
    assetstore = ModelImporter.model('assetstore').getCurrent()
    assetstore_adapter = assetstore_utilities.getAssetstoreAdapter(assetstore)
    fullPath = assetstore_adapter.fullPath(zipFile)

    with ZipFileOpener(fullPath) as (fileList, fileCount):
        with ProgressContext(
                on=True,
                user=user,
                title='Processing "%s"' % zipFile['name'],
                total=fileCount,
                state=ProgressState.ACTIVE,
                current=0) as progress:

            for originalFilePath, originalFileRelpath in fileList:
                originalFileName = os.path.basename(originalFileRelpath)

                progress.update(
                    increment=1,
                    message='Extracting "%s"' % originalFileName)

                with open(originalFilePath, 'rb') as originalFileStream:
                    Image.createImage(
                        imageDataStream=originalFileStream,
                        imageDataSize=os.path.getsize(originalFilePath),
                        originalName=originalFileName,
                        dataset=imagesFolder,
                        creator=user
                    )


def handleCsv(datasetFolder, user, csvFile):
    datasetFolderIds = [
        folder['_id']
        for folder in ModelImporter.model('folder').find({
            'name': datasetFolder['name']
        })
    ]
    # TODO: ensure that datasetFolderIds are UDA folders / in UDA phases

    assetstore = ModelImporter.model('assetstore').getCurrent()
    assetstoreAdapter = assetstore_utilities.getAssetstoreAdapter(assetstore)
    fullPath = assetstoreAdapter.fullPath(csvFile)

    parseErrors = list()
    with open(fullPath, 'rUb') as uploadFileStream,\
        ProgressContext(
            on=True,
            user=user,
            title='Processing "%s"' % csvFile['name'],
            state=ProgressState.ACTIVE,
            message='Parsing CSV') as progress:  # NOQA

        # csv.reader(csvfile, delimiter=',', quotechar='"')
        csvReader = csv.DictReader(uploadFileStream)

        for filenameField in csvReader.fieldnames:
            if filenameField.lower() == 'filename':
                break
        else:
            raise ValidationException('No "filename" field found in CSV.')

        for csvRow in csvReader:
            filename = csvRow.pop(filenameField, None)
            if not filename:
                parseErrors.append(
                    'No "filename" field in row %d' % csvReader.line_num)
                continue

            # TODO: require 'user' to match image creator?
            # TODO: index on meta.originalFilename?
            imageItems = ModelImporter.model('item').find({
                'meta.originalFilename': filename,
                'folderId': {'$in': datasetFolderIds}
            })
            if not imageItems.count():
                parseErrors.append(
                    'No image found with original filename "%s"' % filename)
                continue
            elif imageItems.count() > 1:
                parseErrors.append(
                    'Multiple images found with original filename "%s"' %
                    filename)
                continue
            else:
                imageItem = imageItems.next()

            unstructuredMetadata = imageItem['meta']['unstructured']
            unstructuredMetadata.update(csvRow)
            ModelImporter.model('item').setMetadata(imageItem, {
                'unstructured': unstructuredMetadata
            })

    if parseErrors:
        # TODO: eventually don't store whole string in memory
        parseErrorsStr = '\n'.join(parseErrors)

        parentItem = ModelImporter.model('item').load(
            csvFile['itemId'], force=True)

        upload = ModelImporter.model('upload').createUpload(
            user=getAdminUser(),
            name='parse_errors.txt',
            parentType='item',
            parent=parentItem,
            size=len(parseErrorsStr),
            mimeType='text/plain',
        )
        ModelImporter.model('upload').handleChunk(
            upload, parseErrorsStr)
