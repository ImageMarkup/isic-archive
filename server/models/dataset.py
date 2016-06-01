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
            '_id', 'name', 'description', 'meta', 'created', 'creatorId',
            'updated',
            # TODO: re-add once converted files no longer contributes to size
            # 'size',
        ))

        self.summaryFields = ('_id', 'name', 'updated')

    def loadDatasetCollection(self):
        # assumes collection has been created by provision_utility
        # TODO: cache this value
        return self.model('collection').findOne({'name': 'Lesion Images'})


    def createDataset(self, name, description, creator_user):
        # this may raise a ValidationException if the name already exists
        dataset_folder = self.createFolder(
            parent=self.loadDatasetCollection(),
            name=name,
            description=description,
            parentType='collection',
            public=True,
            creator=creator_user
        )
        dataset_folder = self.copyAccessPolicies(
            src=self.loadDatasetCollection(),
            dest=dataset_folder,
            save=False
        )
        dataset_folder = self.setUserAccess(
            doc=dataset_folder,
            user=creator_user,
            # TODO: make admin
            level=AccessType.READ,
            save=False
        )

        return dataset_folder


    # def addImage(self, study, image_item, creator_user):
    #     for annotator_folder in self.model('folder').find({'parentId': study['_id']}):
    #         self.model('annotation', 'isic_archive').createAnnotation(study, image_item, creator_user, annotator_folder)


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
        dataset_query = {
            'parentId': self.loadDatasetCollection()['_id']
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
        collection = self.model('collection').findOne({'name': 'Phase 0'})
        # TODO: improve error message if folder already exists
        datasetFolder = self.createFolder(
            parent=collection,
            name=name,
            description=description,
            parentType='collection',
            creator=user
        )
        datasetFolder = self.setUserAccess(
            doc=datasetFolder,
            user=user,
            level=AccessType.READ,
            save=False
        )

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
