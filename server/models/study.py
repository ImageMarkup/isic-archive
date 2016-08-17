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

from girder.constants import AccessType
from girder.models.folder import Folder as FolderModel
from girder.models.model_base import ValidationException


class Study(FolderModel):
    class State(object):
        ACTIVE = 'active'
        COMPLETE = 'complete'

    def initialize(self):
        super(Study, self).initialize()
        # TODO: add indexes

        self._filterKeys[AccessType.READ].clear()
        self.exposeFields(level=AccessType.READ, fields=[
            '_id', 'name', 'description', 'created', 'creatorId', 'updated'
        ])
        self.summaryFields = ['_id', 'name', 'updated']
        self.prefixSearchFields = ['lowerName', 'name']

    def loadStudyCollection(self):
        # assumes collection has been created by provision_utility
        # TODO: cache this value
        return self.model('collection').findOne({'name': 'Annotation Studies'})

    def createStudy(self, name, creatorUser, featureset, annotatorUsers,
                    segmentations):
        # this may raise a ValidationException if the name already exists
        studyFolder = self.createFolder(
            parent=self.loadStudyCollection(),
            name=name,
            description='',
            parentType='collection',
            public=None,
            creator=creatorUser
        )
        studyFolder = self.copyAccessPolicies(
            src=self.loadStudyCollection(),
            dest=studyFolder,
            save=False
        )
        studyFolder = self.setUserAccess(
            doc=studyFolder,
            user=creatorUser,
            # TODO: make admin
            level=AccessType.READ,
            save=False
        )
        # "setMetadata" will always save
        studyFolder = self.setMetadata(
            folder=studyFolder,
            metadata={
                'featuresetId': featureset['_id']
            }
        )

        for annotatorUser in annotatorUsers:
            self.addAnnotator(studyFolder, annotatorUser, creatorUser,
                              segmentations)

        return studyFolder

    def addAnnotator(self, study, annotatorUser, creatorUser,
                     segmentations=None):
        Annotation = self.model('annotation', 'isic_archive')
        if not segmentations:
            segmentations = self.getSegmentations(study)

        if self.childAnnotations(
                study=study,
                annotatorUser=annotatorUser).count():
            raise ValidationException(
                'Annotator user is already part of the study.')

        annotatorFolder = self.createFolder(
            parent=study,
            name='%(login)s (%(firstName)s %(lastName)s)' % annotatorUser,
            description='',
            parentType='folder',
            public=True,
            creator=creatorUser
        )
        # study creator accesses will already have been copied to this
        # sub-folder
        # TODO: all users from the study don't need access; this should be
        # changed and migrated
        self.setUserAccess(
            doc=annotatorFolder,
            user=annotatorUser,
            # TODO: make write
            level=AccessType.READ,
            save=True
        )
        self.setMetadata(
            folder=annotatorFolder,
            metadata={
                'userId': annotatorUser['_id']
            }
        )

        for segmentation in segmentations:
            Annotation.createAnnotation(
                study, segmentation, creatorUser, annotatorFolder)

    def addSegmentation(self, study, segmentation, creatorUser):
        Folder = self.model('folder')
        Annotation = self.model('annotation', 'isic_archive')
        for annotatorFolder in Folder.find({'parentId': study['_id']}):
            Annotation.createAnnotation(
                study, segmentation, creatorUser, annotatorFolder)

    def getFeatureset(self, study):
        return self.model('featureset', 'isic_archive').load(
            study['meta']['featuresetId'], exc=True)

    def getAnnotators(self, study, fields=None):
        Folder = self.model('folder')
        User = self.model('user')
        annotatorFolders = Folder.find({'parentId': study['_id']})
        return User.find({
            '_id': {'$in': annotatorFolders.distinct('meta.userId')}
        }, fields=fields)

    def getSegmentations(self, study):
        Annotation = self.model('annotation', 'isic_archive')
        Segmentation = self.model('segmentation', 'isic_archive')
        segmentationIds = Annotation.find(
            {'meta.studyId': study['_id']}).distinct('meta.segmentationId')
        return Segmentation.find({'_id': {'$in': segmentationIds}})

    def getImages(self, study, fields=None):
        Annotation = self.model('annotation', 'isic_archive')
        Image = self.model('image', 'isic_archive')
        imageIds = Annotation.find({
            'meta.studyId': study['_id']}).distinct('meta.imageId')
        return Image.find({'_id': {'$in': imageIds}}, fields=fields)

    def childAnnotations(self, study=None, annotatorUser=None,
                         segmentation=None, imageItem=None, state=None,
                         **kwargs):
        Annotation = self.model('annotation', 'isic_archive')
        query = dict()
        if study:
            query['meta.studyId'] = study['_id']
        if annotatorUser:
            query['meta.userId'] = annotatorUser['_id']
        if segmentation:
            query['meta.segmentationId'] = segmentation['_id']
        if imageItem:
            query['meta.imageId'] = imageItem['_id']
        if state:
            if state == self.State.ACTIVE:
                query['meta.stopTime'] = None
            elif state == self.State.COMPLETE:
                query['meta.stopTime'] = {'$ne': None}
            else:
                raise ValueError('"state" must be "active" or "complete".')
        return Annotation.find(query, **kwargs)

    def _findQueryFilter(self, query, annotatorUser, state):
        studyQuery = {
            'parentId': self.loadStudyCollection()['_id']
        }
        if query:
            studyQuery.update(query)
        if state or annotatorUser:
            annotations = self.childAnnotations(
                annotatorUser=annotatorUser,
                state=state
            )
            studyQuery.update({
                '_id': {'$in': annotations.distinct('meta.studyId')}
            })
        return studyQuery

    def list(self, user=None, limit=0, offset=0, sort=None):
        """
        Return a paginated list of studies that a user may access.
        """
        cursor = self.find({}, sort=sort)
        return self.filterResultsByPermission(
            cursor=cursor, user=user, level=AccessType.READ, limit=limit,
            offset=offset)

    def find(self, query=None, annotatorUser=None, state=None, **kwargs):
        studyQuery = self._findQueryFilter(query, annotatorUser, state)
        return super(Study, self).find(studyQuery, **kwargs)

    def findOne(self, query=None, annotatorUser=None, state=None, **kwargs):
        studyQuery = self._findQueryFilter(query, annotatorUser, state)
        return super(Study, self).findOne(studyQuery, **kwargs)

    def validate(self, doc, **kwargs):
        # TODO: implement
        return super(Study, self).validate(doc, **kwargs)
