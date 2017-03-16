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
        Collection = self.model('collection')
        # assumes collection has been created by provision_utility
        # TODO: cache this value
        return Collection.findOne({'name': 'Annotation Studies'})

    def createStudy(self, name, creatorUser, featureset, annotatorUsers,
                    images):
        Group = self.model('group')
        # this may raise a ValidationException if the name already exists
        studyFolder = self.createFolder(
            parent=self.loadStudyCollection(),
            name=name,
            description='',
            parentType='collection',
            public=False,
            creator=creatorUser,
            allowRename=False
        )
        # Clear all inherited accesses
        studyFolder = self.setAccessList(
            doc=studyFolder,
            access={},
            save=False)
        # Allow study admins to read
        studyFolder = self.setGroupAccess(
            doc=studyFolder,
            group=Group.findOne({'name': 'Study Administrators'}),
            level=AccessType.READ,
            save=False)

        # "setMetadata" will always save
        studyFolder = self.setMetadata(
            folder=studyFolder,
            metadata={
                'featuresetId': featureset['_id']
            }
        )

        for annotatorUser in annotatorUsers:
            studyFolder = self.addAnnotator(
                studyFolder, annotatorUser, creatorUser, images)

        return studyFolder

    def addAnnotator(self, study, annotatorUser, creatorUser,
                     images=None):
        Annotation = self.model('annotation', 'isic_archive')
        Group = self.model('group')
        User = self.model('user', 'isic_archive')

        if not images:
            images = self.getImages(study)

        # Allow annotator to read parent study
        study = self.setUserAccess(
            doc=study,
            user=annotatorUser,
            level=AccessType.READ,
            save=True)

        annotatorFolder = self.createFolder(
            parent=study,
            name=User.obfuscatedName(annotatorUser),
            # Allow a rename, in the rare event of an obfuscated name collision
            allowRename=True,
            description='',
            parentType='folder',
            # Inherit public access state from parent
            public=None,
            creator=creatorUser
        )
        # Clear all inherited accesses
        annotatorFolder = self.setAccessList(
            doc=annotatorFolder,
            access={},
            save=False)
        # Allow study admins to read
        annotatorFolder = self.setGroupAccess(
            doc=annotatorFolder,
            group=Group.findOne({'name': 'Study Administrators'}),
            level=AccessType.READ,
            save=False)
        # Allow annotator to read
        annotatorFolder = self.setUserAccess(
            doc=annotatorFolder,
            user=annotatorUser,
            # TODO: make write?
            level=AccessType.READ,
            save=False)

        # "setMetadata" will always save
        self.setMetadata(
            folder=annotatorFolder,
            metadata={
                'userId': annotatorUser['_id']
            }
        )

        for image in images:
            Annotation.createAnnotation(
                study, image, creatorUser, annotatorFolder)

        # Since parent study could theoretically have changed, return it
        return study

    def addImage(self, study, image, creatorUser):
        Folder = self.model('folder')
        Annotation = self.model('annotation', 'isic_archive')
        for annotatorFolder in Folder.find({'parentId': study['_id']}):
            Annotation.createAnnotation(
                study, image, creatorUser, annotatorFolder)

    def getFeatureset(self, study):
        Featureset = self.model('featureset', 'isic_archive')
        return Featureset.load(study['meta']['featuresetId'], exc=True)

    def getAnnotators(self, study):
        Folder = self.model('folder')
        User = self.model('user', 'isic_archive')
        annotatorFolders = Folder.find({'parentId': study['_id']})
        return User.find({
            '_id': {'$in': annotatorFolders.distinct('meta.userId')}
        })

    def getImages(self, study, fields=None):
        Annotation = self.model('annotation', 'isic_archive')
        Image = self.model('image', 'isic_archive')
        imageIds = Annotation.find({
            'meta.studyId': study['_id']}).distinct('meta.imageId')
        return Image.find({'_id': {'$in': imageIds}}, fields=fields)

    def childAnnotations(self, study=None, annotatorUser=None,
                         image=None, state=None, **kwargs):
        Annotation = self.model('annotation', 'isic_archive')
        query = {}
        if study:
            query['meta.studyId'] = study['_id']
        if annotatorUser:
            query['meta.userId'] = annotatorUser['_id']
        if image:
            query['meta.imageId'] = image['_id']
        if state:
            if state == self.State.ACTIVE:
                query['meta.stopTime'] = None
            elif state == self.State.COMPLETE:
                query['meta.stopTime'] = {'$ne': None}
            else:
                raise ValueError('"state" must be "active" or "complete".')
        return Annotation.find(query, **kwargs)

    def _findQueryFilter(self, query, annotatorUser, state):
        newQuery = query.copy() if query is not None else {}
        newQuery.update({
            'parentId': self.loadStudyCollection()['_id']
        })
        if state or annotatorUser:
            annotations = self.childAnnotations(
                annotatorUser=annotatorUser,
                state=state
            )
            newQuery.update({
                '_id': {'$in': annotations.distinct('meta.studyId')}
            })
        return newQuery

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
