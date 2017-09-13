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
import datetime
import itertools
import os

from girder.constants import AccessType
from girder.models.folder import Folder as FolderModel
from girder.models.model_base import GirderException, ValidationException
from girder.models.notification import ProgressState
from girder.utility import assetstore_utilities, mail_utils
from girder.utility.progress import ProgressContext

from ..upload import ZipFileOpener
from ..utility import generateLines
from ..utility import mail_utils as isic_mail_utils


class Dataset(FolderModel):
    def initialize(self):
        super(Dataset, self).initialize()
        # TODO: add indexes

        self._filterKeys[AccessType.READ].clear()
        self.exposeFields(level=AccessType.READ, fields=[
            '_id', 'name', 'description', 'created', 'creatorId', 'updated',
            # TODO: re-add once converted files no longer contributes to size
            # 'size',
        ])
        self.summaryFields = ['_id', 'name', 'updated']

    def createDataset(self, name, description, creatorUser):
        Collection = self.model('collection')
        Group = self.model('group')

        # This will raise an exception if a duplicate name exists
        datasetFolder = self.createFolder(
            parent=Collection.findOne({'name': 'Lesion Images'}),
            name=name,
            description=description,
            parentType='collection',
            creator=creatorUser,
            public=False,
            allowRename=False,
            reuseExisting=False)
        # Clear all inherited accesses
        datasetFolder = self.setAccessList(
            doc=datasetFolder,
            access={},
            save=False)
        # Allow the creator to read
        datasetFolder = self.setUserAccess(
            doc=datasetFolder,
            user=creatorUser,
            level=AccessType.READ,
            save=False)
        # Allow reviewers to admin (so they can delete the dataset)
        datasetFolder = self.setGroupAccess(
            doc=datasetFolder,
            group=Group.findOne({'name': 'Dataset QC Reviewers'}),
            level=AccessType.ADMIN,
            save=False)

        return self.save(datasetFolder)

    def childImages(self, dataset, limit=0, offset=0, sort=None, filters=None,
                    **kwargs):
        Image = self.model('image', 'isic_archive')

        query = filters.copy() if filters is not None else {}
        query.update({
            'folderId': dataset['_id']
        })

        return Image.find(
            query, limit=limit, offset=offset, sort=sort, **kwargs)

    def _findQueryFilter(self, query):
        Collection = self.model('collection')
        # assumes collection has been created by provision_utility
        # TODO: cache this value
        datasetCollection = Collection.findOne(
            {'name': 'Lesion Images'},
            fields={'_id': 1}
        )

        newQuery = query.copy() if query is not None else {}
        newQuery.update({
            'parentId': datasetCollection['_id']
        })
        return newQuery

    def list(self, user=None, limit=0, offset=0, sort=None):
        """
        Return a paginated list of datasets that a user may access.
        """
        cursor = self.find({}, sort=sort)
        return self.filterResultsByPermission(
            cursor=cursor, user=user, level=AccessType.READ, limit=limit,
            offset=offset)

    def find(self, query=None, **kwargs):
        datasetQuery = self._findQueryFilter(query)
        return super(Dataset, self).find(datasetQuery, **kwargs)

    def findOne(self, query=None, **kwargs):
        datasetQuery = self._findQueryFilter(query)
        return super(Dataset, self).findOne(datasetQuery, **kwargs)

    def filteredSummary(self, image, accessorUser):
        return {
            field: image[field]
            for field in self.summaryFields
        }

    def validate(self, doc, **kwargs):
        # TODO: implement
        # Validate name. This is redundant, because Folder also validates the
        # name, but this allows for a more specific error message.
        doc['name'] = doc['name'].strip()
        if not doc['name']:
            raise ValidationException('Dataset name must not be empty.', 'name')
        return super(Dataset, self).validate(doc, **kwargs)

    def ingestDataset(self, zipFile, user, name, owner, description,
                      license, signature, anonymous, attribution,
                      sendMail=False):
        """
        Ingest an uploaded dataset from a .zip file of images. The images are
        extracted to a "Pre-review" folder within a new dataset folder.
        """
        Folder = self.model('folder')

        # Create dataset folder
        dataset = self.createDataset(name, description, user)

        # Set dataset metadata, including license info
        dataset = self.setMetadata(dataset, {
            'owner': owner,
            'signature': signature,
            'anonymous': anonymous,
            'attribution': attribution,
            'license': license,
            'metadataFiles': []
        })

        prereviewFolder = Folder.createFolder(
            parent=dataset,
            name='Pre-review',
            parentType='folder',
            creator=user,
            public=False)
        prereviewFolder = Folder.copyAccessPolicies(
            dataset, prereviewFolder, save=True)

        # Process zip file
        # TODO: gracefully clean up after exceptions in handleZip
        self._handleZip(prereviewFolder, user, zipFile)

        # Send email confirmations
        if sendMail:
            host = mail_utils.getEmailUrlPrefix()
            params = {
                'group': False,
                'host': host,
                # We intentionally leak full user details here, even though all
                # email recipients may not have access permissions to the user
                'user': user,
                'name': name,
                'owner': owner,
                'description': description,
                'license': license,
                'signature': signature,
                'attribution': 'Anonymous' if anonymous else attribution
            }
            subject = 'ISIC Archive: Dataset Upload Confirmation'
            templateFilename = 'ingestDatasetConfirmation.mako'

            # Mail user
            html = mail_utils.renderTemplate(templateFilename, params)
            mail_utils.sendEmail(to=user['email'], subject=subject, text=html)

            # Mail 'Dataset QC Reviewers' group
            params['group'] = True
            isic_mail_utils.sendEmailToGroup(
                groupName='Dataset QC Reviewers',
                templateFilename=templateFilename,
                templateParams=params,
                subject=subject)

        return dataset

    def _handleZip(self, prereviewFolder, user, zipFile):
        Assetstore = self.model('assetstore')
        Image = self.model('image', 'isic_archive')

        # Get full path of zip file in assetstore
        assetstore = Assetstore.getCurrent()
        assetstore_adapter = assetstore_utilities.getAssetstoreAdapter(
            assetstore)
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
                            parentFolder=prereviewFolder,
                            creator=user
                        )

    def prereviewFolder(self, dataset):
        Folder = self.model('folder')
        return Folder.findOne({
            'name': 'Pre-review',
            'parentId': dataset['_id']
        })

    def reviewImages(self, dataset, acceptedImages, flaggedImages, user):
        Collection = self.model('collection')
        Folder = self.model('folder')
        Image = self.model('image', 'isic_archive')

        # Verify that all images are pending review
        prereviewFolder = self.prereviewFolder(dataset)
        if not prereviewFolder:
            raise GirderException('No Pre-review folder for this dataset.')
        for image in itertools.chain(acceptedImages, flaggedImages):
            if image['folderId'] != prereviewFolder['_id']:
                raise ValidationException(
                    'Image %s is not in Pre-review.' % image['_id'])

        now = datetime.datetime.utcnow()

        for image in acceptedImages:
            image = Image.setMetadata(image, {
                'reviewed': {
                    'userId': user['_id'],
                    'time': now,
                    'accepted': True
                }
            })
            Image.move(image, dataset)

        if flaggedImages:
            flaggedCollection = Collection.findOne({'name': 'Flagged Images'})
            flaggedFolder = Folder.findOne({
                'name': dataset['name'],
                'parentId': flaggedCollection['_id'],
                'parentCollection': 'collection'
            })
            if not flaggedFolder:
                flaggedFolder = Folder.createFolder(
                    parent=flaggedCollection,
                    name=dataset['name'],
                    parentType='collection',
                    public=None,
                    creator=user,
                    allowRename=False,
                    reuseExisting=False)
                flaggedFolder = Folder.copyAccessPolicies(
                    prereviewFolder, flaggedFolder, save=True)
            for image in flaggedImages:
                image = Image.setMetadata(image, {
                    'reviewed': {
                        'userId': user['_id'],
                        'time': now,
                        'accepted': False
                    }
                })
                Image.move(image, flaggedFolder)

        # Remove an empty Pre-review folder
        if (Folder.countItems(prereviewFolder) +
                Folder.countFolders(prereviewFolder)) == 0:
            Folder.remove(prereviewFolder)

    def registerMetadata(self, dataset, metadataFile, user, sendMail=False):
        """Register a .csv file containing metadata about images."""
        # Check if image metadata is already registered
        if self.findOne({'meta.metadataFiles.fileId': metadataFile['_id']}):
            raise ValidationException(
                'Metadata file is already registered on a dataset.')

        # Add image metadata file information to list
        now = datetime.datetime.utcnow()
        metadataFiles = dataset['meta']['metadataFiles']
        metadataFiles.append({
            'fileId': metadataFile['_id'],
            'userId': user['_id'],
            'time': now
        })
        dataset = self.setMetadata(dataset, {
            'metadataFiles': metadataFiles
        })

        # Send email notification
        if sendMail:
            host = mail_utils.getEmailUrlPrefix()
            isic_mail_utils.sendEmailToGroup(
                groupName='Dataset QC Reviewers',
                templateFilename='registerMetadataNotification.mako',
                templateParams={
                    'host': host,
                    'dataset': dataset,
                    'user': user,
                    'metadataFile': metadataFile,
                    'date': now.replace(microsecond=0)
                },
                subject='ISIC Archive: Dataset Metadata Notification')

        return dataset

    def applyMetadata(self, dataset, metadataFile, save):
        """
        Apply metadata in a .csv file to a dataset.
        :return: A list of strings describing parsing or validation errors.
        :rtype: list
        """
        File = self.model('file')

        metadataFileStream = File.download(metadataFile, headers=False)()

        try:
            csvReader = csv.DictReader(generateLines(metadataFileStream))

            if not csvReader.fieldnames:
                raise FileMetadataException(
                    'no field names found on the first line of the CSV')
            for originalNameField in csvReader.fieldnames:
                if originalNameField.strip().lower() == 'filename':
                    break
            else:
                originalNameField = None
            for isicIdField in csvReader.fieldnames:
                if isicIdField.strip().lower() == 'isic_id':
                    break
            else:
                isicIdField = None
            if (not originalNameField) and (not isicIdField):
                raise FileMetadataException(
                    'no "filename" or "isic_id" field found in CSV')

            rowErrors = []
            for rowNum, csvRow in enumerate(csvReader):
                # Offset row number to account for being zero-based and for header row
                rowNum += 2
                try:
                    image = self._getImageForMetadataCsvRow(
                        dataset, csvRow, originalNameField, isicIdField)
                    self._applyMetadataCsvRow(image, csvRow, save)
                except RowMetadataException as e:
                    rowErrors.append('on CSV row %d: %s' % (rowNum, str(e)))
            if rowErrors:
                raise FileMetadataException('\n'.join(rowErrors))
        except csv.Error as e:
            raise FileMetadataException('parsing CSV: %s' % str(e))

        # TODO: return list of error strings, can be empty
        return ['on CSV row 4: unable to parse age',
                'on CSV row 10: unrecognized gender']

    def _getImageForMetadataCsvRow(self, dataset, csvRow, originalNameField,
                                   isicIdField):
        Image = self.model('image', 'isic_archive')

        imageQuery = {
            'folderId': dataset['_id']
            # TODO: match images in the Pre-review folder too
            # 'folderId': {'$in': datasetFolderIds}
        }
        if originalNameField:
            originalName = csvRow.pop(originalNameField, None)
            imageQuery.update({
                'privateMeta.originalFilename': originalName
            })
        else:
            originalName = None
        if isicIdField:
            isicId = csvRow.pop(isicIdField, None)
            imageQuery.update({
                'name': isicId
            })
        else:
            isicId = None

        images = Image.find(imageQuery)
        try:
            if not images.count():
                raise RowMetadataException('no images found')
            if images.count() > 1:
                raise RowMetadataException('multiple images found')
        except RowMetadataException as e:
            if originalNameField and isicIdField:
                errorStr = 'that match both "%s": "%s" and "%s": "%s"' % (
                    originalNameField, originalName, isicIdField, isicId)
            elif originalNameField:
                errorStr = 'that match "%s": "%s"' % (
                    originalNameField, originalName)
            else:  # isicIdField
                errorStr = 'that match "%s": "%s"' % (
                    isicIdField, isicId)
            raise RowMetadataException('%s %s' % (str(e), errorStr))
        image = next(iter(images))
        return image

    def _applyMetadataCsvRow(self, image, csvRow, save):
        pass
        # TODO: ...

        # unstructuredMetadata = image['meta']['unstructured']
        # unstructuredMetadata.update(csvRow)
        # Item.setMetadata(image, {
        #     'unstructured': unstructuredMetadata
        # })


class FileMetadataException(Exception):
    pass


class RowMetadataException(Exception):
    pass


class FieldMetadataException(Exception):
    pass
