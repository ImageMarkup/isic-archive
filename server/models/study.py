#!/usr/bin/env python
# -*- coding: utf-8 -*-

from enum import Enum

from girder.constants import AccessType
from girder.models.folder import Folder


class Study(Folder):

    class State(Enum):
        ACTIVE = 'active'
        COMPLETE = 'complete'

    # TODO: add indexes in "initialize"

    def loadStudyCollection(self):
        # assumes collection has been created by provision_utility
        # TODO: cache this value
        return self.model('collection').findOne({'name': 'Annotation Studies'})


    def createStudy(self, name, creator_user, featureset, annotator_users, image_items):
        # this may raise a ValidationException if the name already exists
        study_folder = self.createFolder(
            parent=self.loadStudyCollection(),
            name=name,
            description='',
            parentType='collection',
            public=None,
            creator=creator_user
        )
        self.copyAccessPolicies(
            src=self.loadStudyCollection(),
            dest=study_folder,
            save=False
        )
        self.setUserAccess(
            doc=study_folder,
            user=creator_user,
            # TODO: make admin
            level=AccessType.READ,
            save=False
        )
        # "setMetadata" will always save
        self.setMetadata(
            folder=study_folder,
            metadata={
                'featuresetId': featureset['_id']
            }
        )

        for annotator_user in annotator_users:
            self.addAnnotator(study_folder, annotator_user, creator_user, image_items)

        return study_folder


    def addAnnotator(self, study, annotator_user, creator_user, image_items=None):
        if not image_items:
            # use one of the existing users (which must exist) as a prototype
            existing_annotator_folder = self.model('folder').findOne({'parentId': study['_id']})
            if not existing_annotator_folder:
                # no image_items and no existing images, so nothing to be done
                return
            image_items = (
                self.model('item').load(annotation_item['meta']['imageId'], force=True)
                for annotation_item in self.model('annotation', 'isic_archive').find({
                    'parentId': existing_annotator_folder['_id']
                })
            )

        annotator_folder = self.model('folder').createFolder(
            parent=study,
            name='%(login)s (%(firstName)s %(lastName)s)' % annotator_user,
            description='',
            parentType='folder',
            public=True,
            creator=creator_user
        )
        # study creator accesses will already have been copied to this sub-folder
        self.model('folder').setUserAccess(
            doc=annotator_folder,
            user=annotator_user,
            # TODO: make write
            level=AccessType.READ,
            save=True
        )
        self.model('folder').setMetadata(
            folder=annotator_folder,
            metadata={
                'userId': annotator_user['_id']
            }
        )

        for image_item in image_items:
            self.model('annotation', 'isic_archive').createAnnotation(study, image_item, creator_user, annotator_folder)


    def addImage(self, study, image_item, creator_user):
        for annotator_folder in self.model('folder').find({'parentId': study['_id']}):
            self.model('annotation', 'isic_archive').createAnnotation(study, image_item, creator_user, annotator_folder)


    def childAnnotations(self, study=None, annotator_user=None, state=None, **kwargs):
        query = {
            'baseParentId': self.loadStudyCollection()['_id']
        }
        if study:
            query['meta.studyId'] = study['_id']
        if state:
            if state == self.State.ACTIVE:
                query['meta.stopTime'] = None
            elif state == self.State.COMPLETE:
                query['meta.stopTime'] = {'$ne': None}
            else:
                raise ValueError('"state" must be an instance of State')
        if annotator_user:
            query['meta.userId'] = annotator_user['_id']
        return self.model('annotation', 'isic_archive').find(query, **kwargs)


    def find(self, query=None, annotator_user=None, state=None, **kwargs):
        study_query = {
            'baseParentId': self.loadStudyCollection()['_id']
        }
        if query:
            study_query.update(query)
        if state or annotator_user:
            annotations = self.childAnnotations(
                annotator_user=annotator_user,
                state=state
            )
            study_query.update({
                '_id': {'$in': annotations.distinct('meta.studyId')}
            })
        return Folder.find(self, study_query, **kwargs)


    def validate(self, doc, **kwargs):
        # TODO: implement
        # raise ValidationException
        return Folder.validate(self, doc, **kwargs)
