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

import datetime
import itertools
import os

import six
from natsort import natsorted

from girder.constants import AccessType
from girder.exceptions import GirderException, ValidationException
from girder.models.collection import Collection
from girder.models.file import File
from girder.models.folder import Folder
from girder.models.group import Group
from girder.models.assetstore import Assetstore
from girder.models.model_base import AccessControlledModel
from girder.models.notification import ProgressState
from girder.utility import assetstore_utilities, mail_utils
from girder.utility.progress import ProgressContext
from backports import csv

from .batch import Batch
from .dataset_helpers import matchFilenameRegex
from .dataset_helpers.image_metadata import addImageMetadata
from .user import User
from ..upload import ZipFileOpener
from ..utility import generateLines
from ..utility import mail_utils as isic_mail_utils


class Dataset(AccessControlledModel):
    def initialize(self):
        self.name = 'dataset'
        # TODO: add indexes

    def createDataset(self, name, description, license, attribution, owner, creatorUser):
        now = datetime.datetime.utcnow()

        # Validate before saving anything
        dataset = self.save({
            # Public informational data
            'name': name,
            'description': description,
            'license': license,
            'attribution': attribution,
            # Public Girder data
            'created': now,
            'updated': now,
            # Private informational data
            'owner': owner,
            'metadataFiles': [],
            # Private Girder data
            'creatorId': creatorUser['_id'],
            'folderId': None,
            'public': False,
            'access': {
                'users': [],
                'groups': []
            }
        })

        # Create folder and add it to the dataset
        datasetFolder = Folder().createFolder(
            parent=Collection().findOne({'name': 'Lesion Images'}),
            name=dataset['name'],
            parentType='collection',
            creator=creatorUser,
            public=dataset['public'],
            allowRename=False,
            reuseExisting=False)
        dataset['folderId'] = datasetFolder['_id']
        self.update(
            {'_id': dataset['_id']},
            {'$set': {'folderId': dataset['folderId']}}
        )

        # Set default accesses (overwriting inherited accesses on the folder)
        dataset = self.setAccessList(
            doc=dataset,
            access={
                'users': [
                    # Allow the creator to write
                    {
                        'id': creatorUser['_id'],
                        'level': AccessType.WRITE,
                        'flags': []
                    }
                ],
                'groups': [
                    # Allow reviewers to admin (so they can delete the dataset)
                    {
                        'id': Group().findOne({'name': 'Dataset QC Reviewers'})['_id'],
                        'level': AccessType.ADMIN,
                        'flags': []
                    }
                ]
            }
        )

        return dataset

    def setUserAccess(self, doc, user, level, save=False, flags=None, currentUser=None,
                      force=False):
        raise NotImplementedError('Use setAccessList instead')

    def setGroupAccess(self, doc, group, level, save=False, flags=None, currentUser=None,
                       force=False):
        raise NotImplementedError('Use setAccessList instead')

    def setAccessList(self, doc, access, save=True, user=None, force=False):
        if not save:
            raise GirderException('"save" must always be True')

        # This will validate "access", and set "doc['access']" to a cleaned list
        doc = super(Dataset, self).setAccessList(doc, access, save=True, user=None, force=True)

        # Set the folder permissions to READ for all named users and groups
        Folder().setAccessList(
            self.imagesFolder(doc),
            {
                'users': [
                    {
                        'id': accessElement['id'],
                        'level': AccessType.READ,
                        'flags': []
                    }
                    for accessElement in doc['access']['users']
                ],
                'groups': [
                    {
                        'id': accessElement['id'],
                        'level': AccessType.READ,
                        'flags': []
                    }
                    for accessElement in doc['access']['groups']
                ]
            },
            save=True,
            # Don't need user, since flags are not set
            user=None,
            force=True
        )

        return doc

    def setPublic(self, doc, public, save=True):
        if not save:
            raise GirderException('"save" must always be True')

        self.update(
            {'_id': doc['_id']},
            {'$set': {'public': public}}
        )
        Folder().update(
            {'_id': doc['folderId']},
            {'$set': {'public': public}}
        )

        return doc

    def filter(self, dataset, user=None, additionalKeys=None):
        # Avoid circular import
        from .image import Image

        level = self.getAccessLevel(dataset, user)

        output = {
            '_id': dataset['_id'],
            '_modelType': 'dataset',
            '_accessLevel': level,
            'name': dataset['name'],
            'description': dataset['description'],
            'license': dataset['license'],
            'attribution': dataset['attribution'],
            'created': dataset['created'],
            'creator': User().filterSummary(
                User().load(dataset['creatorId'], force=True, exc=True),
                user),
            # TODO: verify that "updated" is set correctly
            'updated': dataset['updated'],
            'count': Image().find({'folderId': dataset['folderId']}).count()
        }
        if self.hasAccess(dataset, user, level=AccessType.WRITE):
            output.update({
                'owner': dataset['owner'],
                'metadataFiles': dataset['metadataFiles'],
            })

        return output

    def filterSummary(self, dataset, user=None):
        level = self.getAccessLevel(dataset, user)

        return {
            '_id': dataset['_id'],
            '_accessLevel': level,
            'name': dataset['name'],
            'description': dataset['description'],
            'updated': dataset['updated'],
            'license': dataset['license'],
        }

    def validate(self, doc, **kwargs):
        # Name
        assert isinstance(doc['name'], six.string_types)
        doc['name'] = doc['name'].strip()
        if not doc['name']:
            raise ValidationException('Name must not be empty.', 'name')
        if self.find({
            '_id': {'$ne': doc.get('_id')},
            'name': doc['name']
        }).count():
            raise ValidationException('Name must be unique.', 'name')

        # Description
        assert isinstance(doc['description'], six.string_types)
        doc['description'] = doc['description'].strip()

        # License
        assert isinstance(doc['license'], six.string_types)
        doc['license'] = doc['license'].strip()
        if doc['license'] not in {'CC-0', 'CC-BY', 'CC-BY-NC'}:
            raise ValidationException('Unknown license type.', 'license')

        # Attribution
        assert isinstance(doc['attribution'], six.string_types)
        doc['attribution'] = doc['attribution'].strip()
        if not doc['attribution']:
            raise ValidationException('Attribution must not be empty.', 'attribution')
        if doc['attribution'].lower() in ['anonymous', 'anon']:
            doc['attribution'] = 'Anonymous'
        if doc['attribution'] == 'Anonymous' and doc['license'] != 'CC-0':
            raise ValidationException(
                'Attribution may not be anonymous with a %s license.' % doc['license'],
                'attribution')

        # Owner
        assert isinstance(doc['owner'], six.string_types)
        doc['owner'] = doc['owner'].strip()
        if not doc['owner']:
            raise ValidationException('Owner must not be empty.', 'owner')

        return doc

    def addImage(self, dataset, imageDataStream, imageDataSize, filename, signature, user):
        """
        Add an image to a dataset. The image is stored in a "Pre-review" folder
        within the dataset folder.
        """
        # Avoid circular import
        from .image import Image

        batch = Batch().createBatch(
            dataset=dataset,
            creator=user,
            signature=signature
        )

        prereviewFolder = Folder().createFolder(
            parent=self.imagesFolder(dataset),
            name='Pre-review',
            parentType='folder',
            creator=user,
            public=False,
            reuseExisting=True)

        Image().createImage(
            imageDataStream=imageDataStream,
            imageDataSize=imageDataSize,
            originalName=filename,
            parentFolder=prereviewFolder,
            creator=user,
            dataset=dataset,
            batch=batch
        )

    def addZipBatch(self, dataset, zipFile, signature, user, sendMail=False):
        """
        Ingest an uploaded dataset from a .zip file of images. The images are
        extracted to a "Pre-review" folder within the dataset folder.
        """
        batch = Batch().createBatch(
            dataset=dataset,
            creator=user,
            signature=signature
        )

        prereviewFolder = Folder().createFolder(
            parent=self.imagesFolder(dataset),
            name='Pre-review',
            parentType='folder',
            creator=user,
            public=False,
            reuseExisting=True)

        # Process zip file
        # TODO: gracefully clean up after exceptions in handleZip
        self._handleZip(dataset, batch, prereviewFolder, user, zipFile)

        # Send email confirmations
        if sendMail:
            host = mail_utils.getEmailUrlPrefix()
            params = {
                'group': False,
                'host': host,
                'dataset': dataset,
                # We intentionally leak full user details here, even though all
                # email recipients may not have access permissions to the user
                'user': user,
                'batch': batch,
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

    def _handleZip(self, dataset, batch, prereviewFolder, user, zipFile):
        # Avoid circular import
        from .image import Image

        # Get full path of zip file in assetstore
        assetstore = Assetstore().getCurrent()
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
                        Image().createImage(
                            imageDataStream=originalFileStream,
                            imageDataSize=os.path.getsize(originalFilePath),
                            originalName=originalFileName,
                            parentFolder=prereviewFolder,
                            creator=user,
                            dataset=dataset,
                            batch=batch
                        )

    def imagesFolder(self, dataset):
        return Folder().load(dataset['folderId'], force=True, exc=True)

    def prereviewFolder(self, dataset):
        return Folder().findOne({
            'name': 'Pre-review',
            'parentId': dataset['folderId']
        })

    def reviewImages(self, dataset, acceptedImages, flaggedImages, user):
        # Avoid circular import
        from .image import Image

        # Verify that all images are pending review
        prereviewFolder = self.prereviewFolder(dataset)
        if not prereviewFolder:
            raise GirderException('No Pre-review folder for this dataset.')
        for image in itertools.chain(acceptedImages, flaggedImages):
            if image['folderId'] != prereviewFolder['_id']:
                raise ValidationException(
                    'Image %s is not in Pre-review.' % image['_id'])

        now = datetime.datetime.utcnow()

        imagesFolder = self.imagesFolder(dataset)
        for image in acceptedImages:
            image['meta']['reviewed'] = {
                'userId': user['_id'],
                'time': now,
                'accepted': True
            }
            # '.move' will save the image
            Image().move(image, imagesFolder)

        if flaggedImages:
            flaggedCollection = Collection().findOne({'name': 'Flagged Images'})
            flaggedFolder = Folder().findOne({
                'name': dataset['name'],
                'parentId': flaggedCollection['_id'],
                'parentCollection': 'collection'
            })
            if not flaggedFolder:
                flaggedFolder = Folder().createFolder(
                    parent=flaggedCollection,
                    name=dataset['name'],
                    parentType='collection',
                    public=None,
                    creator=user,
                    allowRename=False,
                    reuseExisting=False)
                flaggedFolder = Folder().copyAccessPolicies(
                    prereviewFolder, flaggedFolder, save=True)
            for image in flaggedImages:
                image['meta']['reviewed'] = {
                    'userId': user['_id'],
                    'time': now,
                    'accepted': False
                }
                # '.move' will save the image
                Image().move(image, flaggedFolder)

        # Remove an empty Pre-review folder
        if (Folder().countItems(prereviewFolder) +
                Folder().countFolders(prereviewFolder)) == 0:
            Folder().remove(prereviewFolder)

    def registerMetadata(self, dataset, metadataFile, user, sendMail=False):
        """Register a .csv file containing metadata about images."""
        # Check if image metadata is already registered
        if self.findOne({'metadataFiles.fileId': metadataFile['_id']}):
            raise ValidationException(
                'Metadata file is already registered on a dataset.')

        # Add image metadata file information to list
        now = datetime.datetime.utcnow()
        dataset['metadataFiles'].append({
            'fileId': metadataFile['_id'],
            'userId': user['_id'],
            'time': now
        })
        dataset = Dataset().save(dataset)

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
        :return: Tuple of:
            - List of strings describing parsing or validation errors.
            - List of strings describing metadata warnings.
        :rtype: tuple(list, list)
        """
        # Avoid circular import
        from .image import Image

        metadataFileStream = File().download(metadataFile, headers=False)()

        images = []
        metadataErrors = []
        metadataWarnings = set()

        try:
            csvReader = csv.DictReader(generateLines(metadataFileStream))

            if not csvReader.fieldnames:
                raise FileMetadataException(
                    'no field names found on the first line of the CSV')
            originalNameField, isicIdField = self._getFilenameFields(csvReader)

            for rowNum, csvRow in enumerate(csvReader):
                # Offset row number to account for being zero-based and for header row
                rowNum += 2
                try:
                    image = self._getImageForMetadataCsvRow(
                        dataset, csvRow, originalNameField, isicIdField)
                    validationErrors, validationWarnings = \
                        addImageMetadata(image, csvRow)

                    # Add row information to validation error strings
                    validationErrors = [
                        'on CSV row %s: %s' % (rowNum, error) for error in validationErrors]
                    metadataErrors.extend(validationErrors)

                    # Update global collection of warnings
                    metadataWarnings.update(validationWarnings)

                    # Add updated image to list of images to potentially save
                    images.append(image)
                except RowMetadataWarning as e:
                    metadataWarnings.add('on CSV row %d: %s' % (rowNum, str(e)))
                except RowMetadataError as e:
                    metadataErrors.append('on CSV row %d: %s' % (rowNum, str(e)))
        except FileMetadataException as e:
            metadataErrors.append(str(e))
        except csv.Error as e:
            metadataErrors.append('parsing CSV: %s' % str(e))
        except UnicodeDecodeError as e:
            metadataErrors.append('CSV is not UTF-8 encoded (%s at position %d in %r)' %
                                  (e.reason, e.start, e.object))

        # Save updated metadata to images
        if not metadataErrors and save:
            for image in images:
                Image().save(image)

        return metadataErrors, natsorted(metadataWarnings)

    def _getFilenameFields(self, csvReader):
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
                'no \'filename\' or \'isic_id\' field found in CSV')
        return originalNameField, isicIdField

    def _getImageForMetadataCsvRow(self, dataset, csvRow, originalNameField,
                                   isicIdField):
        """
        Get the image specified in the CSV row.
        Indicate a warning if no matching images are found.
        Indicate an error if more than one matching images are found.
        """
        # Avoid circular import
        from .image import Image

        imageQuery = {
            # This will match pre-review images too (using 'folderId' will not)
            'meta.datasetId': dataset['_id']
        }
        if originalNameField:
            originalName = csvRow.pop(originalNameField, None)
            originalNameRegex = matchFilenameRegex(originalName)
            imageQuery.update({
                'privateMeta.originalFilename': originalNameRegex
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

        images = Image().find(imageQuery)
        numImages = images.count()
        if numImages != 1:
            if originalNameField and isicIdField:
                errorStr = 'that match both %r: %r and %r: %r' % (
                    originalNameField, originalName, isicIdField, isicId)
            elif originalNameField:
                errorStr = 'that match %r: %r' % (
                    originalNameField, originalName)
            else:  # isicIdField
                errorStr = 'that match %r: %r' % (
                    isicIdField, isicId)

            # No images found
            if numImages == 0:
                raise RowMetadataWarning('%s %s' % ('no images found', errorStr))

            # More than one images found
            raise RowMetadataError('%s %s' % ('multiple images found', errorStr))

        image = next(iter(images))
        return image


class FileMetadataException(Exception):
    pass


class RowMetadataException(Exception):
    pass


class RowMetadataError(RowMetadataException):
    pass


class RowMetadataWarning(RowMetadataException):
    pass
