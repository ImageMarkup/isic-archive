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


    def validate(self, doc):
        # TODO: implement
        # raise ValidationException
        return Item.validate(self, doc)
