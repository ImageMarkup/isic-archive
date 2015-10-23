#!/usr/bin/env python
# -*- coding: utf-8 -*-

from girder.constants import AccessType
from girder.models.folder import Folder


class Dataset(Folder):

    # TODO: add indexes in "initialize"

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

    # TODO: add a "list" method, similar to "Collection.list"

    def find(self, query=None, **kwargs):
        dataset_query = self._find_query_filter(query)
        return Folder.find(self, dataset_query, **kwargs)


    def findOne(self, query=None, **kwargs):
        dataset_query = self._find_query_filter(query)
        return Folder.findOne(self, dataset_query, **kwargs)


    def validate(self, doc, **kwargs):
        # TODO: implement
        # raise ValidationException
        return Folder.validate(self, doc, **kwargs)
