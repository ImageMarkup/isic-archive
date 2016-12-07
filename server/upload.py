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
import six
import sys
import subprocess
import tempfile
import zipfile

from girder.models.model_base import ValidationException
from girder.models.notification import ProgressState
from girder.utility import assetstore_utilities
from girder.utility.model_importer import ModelImporter
from girder.utility.progress import ProgressContext


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


class ParseMetadataCsv:
    """
    Parse a CSV file containing metadata about images in a dataset and validate
    the metadata. Optionally save the validated metadata to the images.
    """
    def __init__(self, dataset, prereviewFolder, user, validator):
        self.user = user
        self.validator = validator

        # Folders where images from this dataset may be
        self.datasetFolderIds = [dataset['_id']]
        if prereviewFolder:
            self.datasetFolderIds.append(prereviewFolder['_id'])

        # Metadata stored after validation, indexed by image item id
        self.validatedMetadata = {}

        # Record image items that have been validated
        self.imageItemIds = set()

        # Final validation results
        self.validationResults = {}

    def validate(self, csvFile):
        Assetstore = ModelImporter.model('assetstore')
        Item = ModelImporter.model('item')

        csvFileName = csvFile['name']
        if csvFileName in self.validationResults:
            raise ValidationException(
                'Already validated CSV file "%s"' % csvFileName)

        assetstore = Assetstore.getCurrent()
        assetstoreAdapter = assetstore_utilities.getAssetstoreAdapter(
            assetstore)
        fullPath = assetstoreAdapter.fullPath(csvFile)

        parseErrors = []
        validationErrors = {}
        with open(fullPath, 'rUb') as uploadFileStream,\
            ProgressContext(
                on=True,
                user=self.user,
                title='Processing "%s"' % csvFileName,
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
                # TODO: index on privateMeta.originalFilename?
                imageItems = Item.find({
                    'privateMeta.originalFilename': filename,
                    'folderId': {'$in': self.datasetFolderIds}
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
                    imageItem = next(iter(imageItems))

                # Expect image to be listed in only one CSV file
                imageItemId = imageItem['_id']
                if imageItemId in self.imageItemIds:
                    parseErrors.append(
                        'Image with original filename "%s" found in multiple '
                        'CSV files' % filename)
                self.imageItemIds.add(imageItemId)

                unstructuredMetadata = imageItem['meta']['unstructured']
                clinicalMetadata = imageItem['meta']['clinical']
                unstructuredMetadata.update(csvRow)
                imageValidationErrors = self.validator(
                    unstructuredMetadata, clinicalMetadata)
                if imageValidationErrors:
                    validationErrors[filename] = imageValidationErrors

                # Store metadata to enable saving to image item later
                self.validatedMetadata[imageItemId] = {
                    'unstructured': unstructuredMetadata,
                    'clinical': clinicalMetadata
                }

        # Store validation result for the CSV file
        validationResult = {}
        if parseErrors:
            validationResult['parseErrors'] = parseErrors
        if validationErrors:
            validationResult['validationErrors'] = validationErrors
        self.validationResults[csvFileName] = validationResult

    def save(self):
        Item = ModelImporter.model('item')

        if not self.validationResults:
            raise ValidationException('Refusing to save unvalidated metadata.')
        if any(('parseErrors' in validationResult or
                'validationErrors' in validationResult)
               for validationResult in self.validationResults):
            raise ValidationException('Refusing to save invalid metadata.')

        for imageItemId, metadata in six.viewitems(self.validatedMetadata):
            imageItem = Item.findOne({'_id': imageItemId})
            if not imageItem:
                raise ValidationException(
                    'Unable to find image: %s' % imageItemId)
            Item.setMetadata(imageItem, metadata)


class MetadataValidationError(Exception):
    """Exception raised for metadata validation errors."""
    def __init__(self, message):
        self.message = message
        Exception.__init__(self, message)


def addImageClinicalMetadata(unstructured, clinical):
    """Parse unstructured metadata to clinical metadata and validate."""
    validationErrors = []
    for parser in [
        _parseAge,
        _parseSex
    ]:
        try:
            parser(unstructured, clinical)
        except MetadataValidationError as e:
            validationErrors.append(str(e))
    return validationErrors


def _getOneFrom(containerDict, allowedSet):
    foundSet = set(six.viewkeys(containerDict)) & allowedSet
    if not foundSet:
        return None
    elif len(foundSet) == 1:
        return containerDict.pop(foundSet.pop())
    else:
        raise MetadataValidationError(
            'only one of %s may be present' % sorted(foundSet))


def _assertInt(value):
    try:
        value = int(float(value))
    except ValueError:
        raise MetadataValidationError(
            'value of "%s" must be an integer' % value)
    return value


def _assertEnumerated(value, allowed):
    if value not in allowed:
        raise MetadataValidationError(
            'value of "%s" must be one of: %s' % (value, sorted(allowed)))
    return value


def _parseAge(unstructured, clinical):
    value = unstructured.pop('age', None)
    if value is not None:
        if value in ['', 'unknown']:
            value = None
        else:
            if value == '85+':
                value = '85'
            value = _assertInt(value)
            if value > 85:
                # TODO: 99 is used as a placeholder for unknown in existing
                # images
                value = 85
        clinical['age'] = value

    # Drop deprecated fields
    unstructured.pop('age_categ', None)


def _parseSex(unstructured, clinical):
    value = _getOneFrom(unstructured, {'sex', 'gender'})
    if value is not None:
        value = value.lower()
        if value in ['', 'unknown']:
            value = None
        elif value == 'm':
            value = 'male'
        elif value == 'f':
            value = 'female'
        _assertEnumerated(value, {'male', 'female', None})
        clinical['sex'] = value
