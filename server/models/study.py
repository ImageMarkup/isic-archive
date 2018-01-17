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

from girder.constants import AccessType, SortDir
from girder.exceptions import ValidationException
from girder.models.collection import Collection
from girder.models.folder import Folder
from girder.models.group import Group

from .featureset import Featureset
from .image import Image
from .user import User


class Study(Folder):
    class State(object):
        ACTIVE = 'active'
        COMPLETE = 'complete'

    def initialize(self):
        super(Study, self).initialize()
        # TODO: add indexes

        self.prefixSearchFields = ['lowerName', 'name']

    def loadStudyCollection(self):
        # assumes collection has been created by provision_utility
        # TODO: cache this value
        return Collection().findOne({'name': 'Annotation Studies'})

    def createStudy(self, name, creatorUser, featureset, annotatorUsers,
                    images):
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
            group=Group().findOne({'name': 'Study Administrators'}),
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
        # Avoid circular import
        from .annotation import Annotation

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
            name=User().obfuscatedName(annotatorUser),
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
            group=Group().findOne({'name': 'Study Administrators'}),
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
            Annotation().createAnnotation(
                study, image, creatorUser, annotatorFolder)

        # Since parent study could theoretically have changed, return it
        return study

    def removeAnnotator(self, study, annotatorUser):
        annotatorFolder = Folder().findOne({
            'parentId': study['_id'],
            'meta.userId': annotatorUser['_id']
        })
        if not annotatorFolder:
            raise ValidationException('Annotator user is not in study.')
        Folder().remove(annotatorFolder)

    def addImage(self, study, image, creatorUser):
        # Avoid circular import
        from .annotation import Annotation

        for annotatorFolder in Folder().find({'parentId': study['_id']}):
            Annotation().createAnnotation(
                study, image, creatorUser, annotatorFolder)

    def getFeatureset(self, study):
        return Featureset().load(study['meta']['featuresetId'], exc=True)

    def getAnnotators(self, study):
        annotatorFolders = Folder().find({'parentId': study['_id']})
        return User().find({
            '_id': {'$in': annotatorFolders.distinct('meta.userId')}
        })

    def getImages(self, study):
        # Avoid circular import
        from .annotation import Annotation

        imageIds = Annotation().find({
            'meta.studyId': study['_id']}).distinct('meta.imageId')
        return Image().find({'_id': {'$in': imageIds}})

    def childAnnotations(self, study=None, annotatorUser=None,
                         image=None, state=None, **kwargs):
        # Avoid circular import
        from .annotation import Annotation

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
        return Annotation().find(query, **kwargs)

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

    def filter(self, study, user=None, additionalKeys=None):
        # Avoid circular import
        from .annotation import Annotation

        output = {
            '_id': study['_id'],
            '_modelType': 'study',
            'name': study['name'],
            'description': study['description'],
            'created': study['created'],
            'creator': User().filterSummary(
                User().load(study['creatorId'], force=True, exc=True),
                user),
            # TODO: verify that "updated" is set correctly
            'updated': study['updated'],
            'featureset': Featureset().load(
                id=study['meta']['featuresetId'],
                fields=Featureset().summaryFields, exc=True),
            'users': sorted(
                (
                    User().filterSummary(annotatorUser, user)
                    for annotatorUser in
                    Study().getAnnotators(study)
                ),
                # Sort by the obfuscated name
                key=lambda annotatorUser: annotatorUser['name']
            ),
            'images': list(
                Image().filterSummary(image, user)
                for image in
                Study().getImages(study).sort('name', SortDir.ASCENDING)
            ),
            'userCompletion': {
                str(annotatorComplete['_id']): annotatorComplete['count']
                for annotatorComplete in
                Annotation().collection.aggregate([
                    {'$match': {
                        'meta.studyId': study['_id'],
                    }},
                    {'$group': {
                        '_id': '$meta.userId',
                        'count': {'$sum': {'$cond': {
                            'if': '$meta.stopTime',
                            'then': 1,
                            'else': 0
                        }}}
                    }}
                ])
            }
        }

        return output

    def filterSummary(self, study, user=None):
        return {
            '_id': study['_id'],
            'name': study['name'],
            'description': study['description'],
            'updated': study['updated'],
        }

    def validate(self, doc, **kwargs):
        # TODO: implement
        return super(Study, self).validate(doc, **kwargs)
