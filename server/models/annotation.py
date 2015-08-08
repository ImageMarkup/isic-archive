#!/usr/bin/env python
# -*- coding: utf-8 -*-

from girder.models.item import Item


class Annotation(Item):

    def createAnnotation(self, study, image_item, creator_user, annotator_folder):
        annotation_item = self.createItem(
            folder=annotator_folder,
            name=image_item['name'],
            description='',
            creator=creator_user
        )
        # "setMetadata" will always save
        self.setMetadata(
            item=annotation_item,
            metadata={
                'studyId': study['_id'],
                'userId': annotator_folder['meta']['userId'],
                'imageId': image_item['_id'],
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
