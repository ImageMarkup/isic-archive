#!/usr/bin/env python
# -*- coding: utf-8 -*-

import mimetypes

from girder.constants import AccessType
from girder.models.folder import Folder
from girder.models.model_base import ValidationException

from ..upload import handleCsv, handleImage, handleZip

ZIP_FORMATS = [
    'multipart/x-zip',
    'application/zip',
    'application/zip-compressed',
    'application/x-zip-compressed',
]

CSV_FORMATS = [
    'text/csv',
    'application/vnd.ms-excel'
]


class Dataset(Folder):

    def initialize(self):
        super(Dataset, self).initialize()
        # TODO: add indexes

        self._filterKeys[AccessType.READ].clear()
        self.exposeFields(level=AccessType.READ, fields=(
            '_id', 'name', 'description', 'created', 'creatorId', 'updated',
            # TODO: re-add once converted files no longer contributes to size
            # 'size',
        ))
        self.summaryFields = ('_id', 'name', 'updated')


    def createDataset(self, name, description, creatorUser):
        # Look for duplicate names in any of the dataset-containing collections
        datasetCollectionIds = self.model('collection').find({
            'name': {'$in': [
                'Phase 0',
                'Flagged Images',
                'Phase 1a',
                'Phase 1b',
                'Lesion Images'
            ]}
        }).distinct('_id')
        if self.model('folder').find({
            'name': name,
            'parentId': {'$in': datasetCollectionIds}
        }).count():
            raise ValidationException(
                'A dataset with this name already exists.')

        datasetFolder = self.createFolder(
            parent=self.model('collection').findOne({'name': 'Phase 0'}),
            name=name,
            description=description,
            parentType='collection',
            creator=creatorUser
        )
        # The uploader may already have greater access via inheritance from
        # Phase 0, which should not be overwritten
        if not self.hasAccess(datasetFolder, creatorUser, AccessType.READ):
            datasetFolder = self.setUserAccess(
                doc=datasetFolder,
                user=creatorUser,
                # TODO: make admin
                level=AccessType.READ,
                save=False
            )
        return self.save(datasetFolder)


    def childImages(self, dataset, limit=0, offset=0, sort=None, filters=None,
                   **kwargs):
        if not filters:
            filters = {}

        q = {
            'folderId': dataset['_id']
        }
        q.update(filters)

        return self.model('image', 'isic_archive').find(
            q, limit=limit, offset=offset, sort=sort, **kwargs)

    def _find_query_filter(self, query):
        # assumes collection has been created by provision_utility
        # TODO: cache this value
        dataset_collection = self.model('collection').findOne({
            'name': 'Lesion Images'})

        dataset_query = {
            'parentId': dataset_collection['_id']
        }
        if query:
            dataset_query.update(query)
        return dataset_query

    def list(self, user=None, limit=0, offset=0, sort=None):
        """
        Return a paginated list of datasets that a user may access.
        """
        cursor = self.find({}, sort=sort)
        return self.filterResultsByPermission(
            cursor=cursor, user=user, level=AccessType.READ, limit=limit,
            offset=offset)

    def find(self, query=None, **kwargs):
        dataset_query = self._find_query_filter(query)
        return Folder.find(self, dataset_query, **kwargs)


    def findOne(self, query=None, **kwargs):
        dataset_query = self._find_query_filter(query)
        return Folder.findOne(self, dataset_query, **kwargs)


    def validate(self, doc, **kwargs):
        # TODO: implement
        # raise ValidationException

        # Validate name. This is redundant, because Folder also validates the
        # name, but this allows for a more specific error message.
        doc['name'] = doc['name'].strip()
        if not doc['name']:
            raise ValidationException('Dataset name must not be empty.', 'name')
        return Folder.validate(self, doc, **kwargs)

    def ingestDataset(self, uploadFolder, user, name, description, license,
            signature, anonymous, attribution):
        """
        Ingest an uploaded dataset. This upload folder is expected to contain a
        .zip file of images and a .csv file that contains metadata about the
        images. The images are extracted to a new folder in the "Phase 0"
        collection and then processed.
        """
        if not uploadFolder:
            raise ValidationException(
                'No files were uploaded.', 'uploadFolder')

        zipFileItems = [f for f in self.model('folder').childItems(uploadFolder)
                        if mimetypes.guess_type(f['name'], strict=False)[0] in
                        ZIP_FORMATS]
        if not zipFileItems:
            raise ValidationException(
                'No .zip files were uploaded.', 'uploadFolder')

        csvFileItems = [f for f in self.model('folder').childItems(uploadFolder)
                        if mimetypes.guess_type(f['name'], strict=False)[0] in
                        CSV_FORMATS]
        if not csvFileItems:
            raise ValidationException(
                'No .csv files were uploaded.', 'uploadFolder')

        # Create dataset folder
        datasetFolder = self.createDataset(name, description, user)

        # Set dataset license agreement metadata
        datasetFolder = self.setMetadata(datasetFolder, {
            'signature': signature,
            'anonymous': anonymous,
            'attribution': attribution
        })

        # Process zip files
        for item in zipFileItems:
            zipFiles = self.model('item').childFiles(item)
            for zipFile in zipFiles:
                # TODO: gracefully clean up after exceptions in handleZip
                handleZip(datasetFolder, user, zipFile)

        # Process extracted images
        for item in self.childImages(datasetFolder):
            handleImage(item, user, license)

        # Process metadata in CSV files
        for item in csvFileItems:
            csvFiles = self.model('item').childFiles(item)
            for csvFile in csvFiles:
                handleCsv(datasetFolder, user, csvFile)

        # Move metadata item to dataset folder. This preserves any parsing
        # errors that were added to the item for review.
        for item in csvFileItems:
            self.model('item').move(item, datasetFolder)

        # Delete uploaded files
        # self.model('folder').clean(uploadFolder)

        return datasetFolder
