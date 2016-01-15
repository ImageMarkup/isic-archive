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


    def createStudy(self, name, creator_user, featureset, annotator_users, segmentations):
        # this may raise a ValidationException if the name already exists
        study_folder = self.createFolder(
            parent=self.loadStudyCollection(),
            name=name,
            description='',
            parentType='collection',
            public=None,
            creator=creator_user
        )
        study_folder = self.copyAccessPolicies(
            src=self.loadStudyCollection(),
            dest=study_folder,
            save=False
        )
        study_folder = self.setUserAccess(
            doc=study_folder,
            user=creator_user,
            # TODO: make admin
            level=AccessType.READ,
            save=False
        )
        # "setMetadata" will always save
        study_folder = self.setMetadata(
            folder=study_folder,
            metadata={
                'featuresetId': featureset['_id']
            }
        )

        for annotator_user in annotator_users:
            self.addAnnotator(study_folder, annotator_user, creator_user, segmentations)

        return study_folder


    def addAnnotator(self, study, annotator_user, creator_user, segmentations=None):
        if not segmentations:
            raise Exception('No list of segmentatoins provided')
            # TODO: add a "getSegmentations" method to attempt to look them up
            segmentations = self.getImages(study)

        annotator_folder = self.model('folder').createFolder(
            parent=study,
            name='%(login)s (%(firstName)s %(lastName)s)' % annotator_user,
            description='',
            parentType='folder',
            public=True,
            creator=creator_user
        )
        # study creator accesses will already have been copied to this sub-folder
        # TODO: all users from the study don't need access; this should be changed and migrated
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

        for segmentation in segmentations:
            self.model('annotation', 'isic_archive').createAnnotation(study, segmentation, creator_user, annotator_folder)


    def addImage(self, study, segmentation, creator_user):
        for annotator_folder in self.model('folder').find({'parentId': study['_id']}):
            self.model('annotation', 'isic_archive').createAnnotation(study, segmentation, creator_user, annotator_folder)


    def getAnnotators(self, study):
        annotator_folders = self.model('folder').find({'parentId': study['_id']})
        return self.model('user').find({
            '_id': {'$in': annotator_folders.distinct('meta.userId')}
        })


    def getImages(self, study):
        image_ids = self.model('annotation', 'isic_archive').find({
            'meta.studyId': study['_id']
        }).distinct('meta.imageId')
        return self.model('image', 'isic_archive').find({
            '_id': {'$in': image_ids}
        })


    def childAnnotations(self, study=None, annotator_user=None,
                         segmentation=None, image_item=None, state=None,
                         **kwargs):
        query = dict()
        if study:
            query['meta.studyId'] = study['_id']
        if annotator_user:
            query['meta.userId'] = annotator_user['_id']
        if segmentation:
            query['meta.segmentationId'] = segmentation['_id']
        if image_item:
            query['meta.imageId'] = image_item['_id']
        if state:
            if state == self.State.ACTIVE:
                query['meta.stopTime'] = None
            elif state == self.State.COMPLETE:
                query['meta.stopTime'] = {'$ne': None}
            else:
                raise ValueError('"state" must be an instance of State')
        return self.model('annotation', 'isic_archive').find(query, **kwargs)


    def _find_query_filter(self, query, annotator_user, state):
        study_query = {
            'parentId': self.loadStudyCollection()['_id']
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
        return study_query


    def find(self, query=None, annotator_user=None, state=None, **kwargs):
        study_query = self._find_query_filter(query, annotator_user, state)
        return Folder.find(self, study_query, **kwargs)


    def findOne(self, query=None, annotator_user=None, state=None, **kwargs):
        study_query = self._find_query_filter(query, annotator_user, state)
        return Folder.findOne(self, study_query, **kwargs)


    def validate(self, doc, **kwargs):
        # TODO: implement
        # raise ValidationException
        return Folder.validate(self, doc, **kwargs)
