#!/usr/bin/env python
# -*- coding: utf-8 -*-

from girder.constants import AccessType
from girder.models.item import Item


class Annotation(Item):

    def createAnnotation(self, study, segmentation, creator_user, annotator_folder):
        image = self.model('image', 'isic_archive').load(
            segmentation['imageId'], user=creator_user, level=AccessType.READ)

        annotation_item = self.createItem(
            folder=annotator_folder,
            name=image['name'],
            description='',
            creator=creator_user
        )
        # "setMetadata" will always save
        self.setMetadata(
            item=annotation_item,
            metadata={
                'studyId': study['_id'],
                'userId': annotator_folder['meta']['userId'],
                'segmentationId': segmentation['_id'],
                'imageId': image['_id'],
                'startTime': None,
                'stopTime': None,
                'annotations': None
            }
        )
        return annotation_item


    def _find_query_filter(self, query):
        annotation_query = {
            'baseParentId': self.model('study', 'isic_archive').loadStudyCollection()['_id']
        }
        if query:
            annotation_query.update(query)
        return annotation_query


    def find(self, query=None, **kwargs):
        annotation_query = self._find_query_filter(query)
        return Item.find(self, annotation_query, **kwargs)


    def findOne(self, query=None, **kwargs):
        annotation_query = self._find_query_filter(query)
        return Item.findOne(self, annotation_query, **kwargs)


    def validate(self, doc):
        # TODO: implement
        # raise ValidationException
        return Item.validate(self, doc)
