import csv
import datetime
import io
import itertools
import json
import time
from typing import List, Tuple

import botocore
import cherrypy
from natsort import natsorted

from girder.constants import AccessType
from girder.exceptions import GirderException, RestException, ValidationException
from girder.models.collection import Collection
from girder.models.file import File
from girder.models.folder import Folder
from girder.models.group import Group
from girder.models.model_base import AccessControlledModel
from girder.models.upload import Upload
from girder.utility import mail_utils

from isic_archive import settings
from .batch import Batch
from .dataset_helpers import matchFilenameRegex
from .dataset_helpers.image_metadata import addImageMetadata
from .user import User
from ..utility import mail_utils as isic_mail_utils
from ..utility.boto import s3, sts


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

    def remove(self, dataset, **kwargs):
        # Avoid circular import
        from .image import Image

        for image in Image().find({'meta.datasetId': dataset['_id']}):
            Image().remove(image)

        for metadataFileInfo in dataset['metadataFiles']:
            metadataFile = File().load(metadataFileInfo['fileId'], force=True, exc=True)
            self.removeMetadata(dataset, metadataFile)

        for batch in Batch().find({'datasetId': dataset['_id']}):
            Batch().remove(batch)

        imagesFolder = self.imagesFolder(dataset)
        Folder().remove(imagesFolder)

        flaggedCollection = Collection().findOne({'name': 'Flagged Images'})
        flaggedFolder = Folder().findOne({
            'name': dataset['name'],
            'parentId': flaggedCollection['_id'],
            'parentCollection': 'collection'
        })
        if flaggedFolder:
            # TODO: If there are any flagged images with segmentations, those won't be removed
            Folder().remove(flaggedFolder)

        return super(Dataset, self).remove(dataset)

    def validate(self, doc, **kwargs):
        # Name
        assert isinstance(doc['name'], str)
        doc['name'] = doc['name'].strip()
        if not doc['name']:
            raise ValidationException('Name must not be empty.', 'name')
        if self.find({
            '_id': {'$ne': doc.get('_id')},
            'name': doc['name']
        }).count():
            raise ValidationException('Name must be unique.', 'name')

        # Description
        assert isinstance(doc['description'], str)
        doc['description'] = doc['description'].strip()

        # License
        assert isinstance(doc['license'], str)
        doc['license'] = doc['license'].strip()
        if doc['license'] not in {'CC-0', 'CC-BY', 'CC-BY-NC', 'CC-BY-NC-SA'}:
            raise ValidationException('Unknown license type.', 'license')

        # Attribution
        assert isinstance(doc['attribution'], str)
        doc['attribution'] = doc['attribution'].strip()
        if not doc['attribution']:
            raise ValidationException('Attribution must not be empty.', 'attribution')
        if doc['attribution'].lower() in ['anonymous', 'anon']:
            doc['attribution'] = 'Anonymous'
        if doc['attribution'] == 'Anonymous' and doc['license'] != 'CC-0':
            raise ValidationException(
                f'Attribution may not be anonymous with a {doc["license"]} license.',
                'attribution')

        # Owner
        assert isinstance(doc['owner'], str)
        doc['owner'] = doc['owner'].strip()
        if not doc['owner']:
            raise ValidationException('Owner must not be empty.', 'owner')

        return doc

    def addImage(self, dataset, imageDataStream, imageDataSize, filename, signature, user):
        """
        Add an image to a dataset.

        The image is stored in a "Pre-review" folder within the dataset folder.
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

        image = Image().createImage(
            imageDataStream=imageDataStream,
            imageDataSize=imageDataSize,
            originalFileRelpath=filename,
            parentFolder=prereviewFolder,
            creator=user,
            dataset=dataset,
            batch=batch
        )

        return image

    def initiateZipUploadS3(self, dataset, signature, user):
        """Initiate a direct-to-S3 upload of a ZIP file of images."""  # noqa: D401
        # Create new batch
        batch = Batch().createBatch(
            dataset=dataset,
            creator=user,
            signature=signature)

        # Add policy that restricts uploads to only the specific key
        s3BucketArn = f'arn:aws:s3:::{settings.ISIC_UPLOAD_BUCKET_NAME}'
        s3ObjectKey = f'zip-uploads/{batch["_id"]}'
        s3BucketPutObjectInKeyPolicy = {
            'Version': '2012-10-17',
            'Statement': [
                {
                    'Effect': 'Allow',
                    'Action': [
                        's3:PutObject',
                    ],
                    'Resource': f'{s3BucketArn}/{s3ObjectKey}'
                }
            ]
        }

        # Get temporary security credentials with permission to upload into the
        # object in the S3 bucket. The AWS Security Token Service (STS) provides
        # the credentials when the machine assumes the upload role.
        try:
            resp = sts.assume_role(
                RoleArn=settings.ISIC_UPLOAD_ROLE_ARN,
                RoleSessionName='ZipUploadSession-%d' % int(time.time()),
                Policy=json.dumps(s3BucketPutObjectInKeyPolicy),
                # 12 hours, also limited by the MaxSessionDuration of the role
                DurationSeconds=12 * 60 * 60
            )
        except botocore.exceptions.ClientError as e:
            raise GirderException(
                f'Error acquiring temporary security credentials: {e.response["Error"]["Message"]}')

        # TODO: Could store assumed role user ARN on batch for use as principal in a bucket policy
        # that effectively revokes the temporary security credentials, before they expire,
        # on cancel/finalize:
        # https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_temp_control-access_disable-perms.html
        # assumedRoleUserArn = resp['AssumedRoleUser']['Arn']

        credentials = resp['Credentials']

        # Store upload information on batch
        batch.update({
            's3BucketName': settings.ISIC_UPLOAD_BUCKET_NAME,
            's3ObjectKey': s3ObjectKey,
            'ingestStatus': 'uploading'
        })
        batch = Batch().save(batch)

        return {
            'accessKeyId': credentials['AccessKeyId'],
            'secretAccessKey': credentials['SecretAccessKey'],
            'sessionToken': credentials['SessionToken'],
            'bucketName': settings.ISIC_UPLOAD_BUCKET_NAME,
            'objectKey': s3ObjectKey,
            'batchId': batch['_id']
        }

    def cancelZipUploadS3(self, dataset, batch, user):
        """Cancel a direct-to-S3 upload of a ZIP file of images."""
        # Get upload information stored on batch
        s3BucketName = batch.get('s3BucketName')
        s3ObjectKey = batch.get('s3ObjectKey')
        if not all([s3BucketName, s3ObjectKey]):
            raise GirderException('Error retrieving upload information.')

        # Delete file from S3 as upload user
        try:
            s3.delete_object(
                Bucket=s3BucketName,
                Key=s3ObjectKey
            )
        except botocore.exceptions.ClientError as e:
            raise GirderException(f'Error deleting object: {e.response["Error"]["Message"]}')

        Batch().remove(batch)

    def finalizeZipUploadS3(self, batch):
        """
        Finalize a direct-to-S3 upload of a ZIP file of images.

        This involves several steps:
        - Download the ZIP file from S3 and add it as a file attached to the dataset.
        - Delete the ZIP file from S3.
        - Ingest images from the ZIP file into the dataset.
        """
        # avoid circular imports from the models __init__
        from isic_archive.tasks import ingestBatchFromZipfile
        updateResult = Batch().collection.update_one(
            {
                '_id': batch['_id'],
                'ingestStatus': 'uploading',
            },
            {
                '$set': {'ingestStatus': 'queued'}
            }
        )
        if updateResult.modified_count != 1:
            raise RestException("Trying to finalize a batch which isn't uploading", code=409)

        # Ingest images from ZIP file into dataset
        ingestBatchFromZipfile.delay(batch['_id'])
        cherrypy.response.status = 201

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
                    f'Image {image["_id"]} is not in Pre-review.')

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
        if (Folder().countItems(prereviewFolder) + Folder().countFolders(prereviewFolder)) == 0:
            Folder().remove(prereviewFolder)

    def registerMetadata(self, dataset, metadataDataStream, filename, user, sendMail=False):
        """Register CSV data containing metadata about images."""
        # Store metadata data in a .csv file attached to the dataset
        metadataFile = Upload().uploadFromFile(
            obj=metadataDataStream,
            size=len(metadataDataStream),
            name=filename,
            parentType='dataset',
            parent=dataset,
            attachParent=True,
            user=user,
            mimeType='text/csv'
        )
        # TODO: remove this once a bug in upstream Girder is fixed
        metadataFile['attachedToType'] = ['dataset', 'isic_archive']
        metadataFile = File().save(metadataFile)

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

    def removeMetadata(self, dataset, metadataFile):
        # Remove metadata file registration from database
        self.update(
            {'_id': dataset['_id']},
            {'$pull': {'metadataFiles': {'fileId': metadataFile['_id']}}}
        )

        # Remove file
        File().remove(metadataFile)

        # Update document in-place
        dataset['metadataFiles'][:] = [registration for registration in dataset['metadataFiles']
                                       if registration['fileId'] != metadataFile['_id']]
        return dataset

    def applyMetadata(self, dataset, metadataFile, save) -> Tuple[List[str], List[str]]:
        """
        Apply metadata in a .csv file to a dataset.

        :return: Tuple of:
            - List of strings describing parsing or validation errors.
            - List of strings describing metadata warnings.
        """
        # Avoid circular import
        from .image import Image

        metadataFileStream = io.BytesIO()
        for chunk in File().download(metadataFile, headers=False)():
            metadataFileStream.write(chunk)
        metadataFileStream.seek(0)

        images = []
        metadataErrors = []
        metadataWarnings = set()

        try:
            csvReader = csv.DictReader(io.TextIOWrapper(
                buffer=metadataFileStream,
                # This will behave as 'utf-8' if no BOM is present
                encoding='utf-8-sig',
                # The CSV reader will parse newlines
                newline='',
            ))

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
                        f'on CSV row {rowNum}: {error}'
                        for error in validationErrors]
                    metadataErrors.extend(validationErrors)

                    # Update global collection of warnings
                    metadataWarnings.update(validationWarnings)

                    # Add updated image to list of images to potentially save
                    images.append(image)
                except RowMetadataWarning as e:
                    metadataWarnings.add(f'on CSV row {rowNum:d}: {str(e)}')
                except RowMetadataError as e:
                    metadataErrors.append(f'on CSV row {rowNum:d}: {str(e)}')
        except FileMetadataException as e:
            metadataErrors.append(str(e))
        except csv.Error as e:
            metadataErrors.append(f'parsing CSV: {str(e)}')
        except UnicodeDecodeError as e:
            metadataErrors.append(
                f'CSV is not UTF-8 encoded ({e.reason} at position {e.start:d} in {e.object!r})')

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
                "no 'filename' or 'isic_id' field found in CSV")
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
                errorStr = f'that match both {originalNameField!r}: ' \
                    f'{originalName!r} and {isicIdField!r}: {isicId!r}'
            elif originalNameField:
                errorStr = f'that match {originalNameField!r}: {originalName!r}'
            else:  # isicIdField
                errorStr = f'that match {isicIdField!r}: {isicId!r}'

            # No images found
            if numImages == 0:
                raise RowMetadataWarning(f'no images found {errorStr}')

            # More than one images found
            raise RowMetadataError(f'multiple images found {errorStr}')

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
