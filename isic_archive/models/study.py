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

import json
import os

import jsonschema

from girder.constants import AccessType, SortDir
from girder.exceptions import ValidationException
from girder.models.collection import Collection
from girder.models.folder import Folder
from girder.models.group import Group

from .image import Image
from .user import User


_masterFeaturesPath = 'masterFeatures.json'
with open(os.path.join(os.path.dirname(__file__),
                       _masterFeaturesPath), 'rb') as _masterFeaturesStream:
    MASTER_FEATURES = [
        feature['id'] for feature in json.load(_masterFeaturesStream)
    ]


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

    def createStudy(self, name, creatorUser, questions, features, annotatorUsers, images):
        # Avoid circular import
        from .annotation import Annotation

        # validate the new questions and features before anything else
        studyMeta = {
            'questions': questions,
            'features': features,
            'participationRequests': []
        }
        self.validate({'meta': studyMeta})

        try:
            study = self.createFolder(
                parent=self.loadStudyCollection(),
                name=name,
                description='',
                parentType='collection',
                public=False,
                creator=creatorUser,
                allowRename=False
            )
        except ValidationException as e:
            # Reword the validation error message
            if e.message == 'A folder with that name already exists here.':
                raise ValidationException('A study with that name already exists.', 'name')
            else:
                raise

        # Clear all inherited accesses
        study = self.setAccessList(
            doc=study,
            access={},
            save=False)
        # Allow study admins to read
        study = self.setGroupAccess(
            doc=study,
            group=Group().findOne({'name': 'Study Administrators'}),
            level=AccessType.READ,
            save=False)
        # Allow annotators to read study (since annotations delegate their access to study)
        for annotatorUser in annotatorUsers:
            study = self.setUserAccess(
                doc=study,
                user=annotatorUser,
                level=AccessType.READ,
                save=False)

        study['meta'] = studyMeta
        study = self.save(study)

        for annotatorUser in annotatorUsers:
            for image in images:
                Annotation().createAnnotation(study, image, annotatorUser)

        return study

    def addAnnotator(self, study, annotatorUser):
        # Avoid circular import
        from .annotation import Annotation

        # Allow annotator to read parent study
        study = self.setUserAccess(
            doc=study,
            user=annotatorUser,
            level=AccessType.READ,
            save=True)

        # Remove request from the user to participate in the study
        study = self.removeParticipationRequest(study, annotatorUser)

        for image in self.getImages(study):
            Annotation().createAnnotation(study, image, annotatorUser)

        # Since parent study could have changed, return it
        return study

    def removeAnnotator(self, study, annotatorUser):
        # Avoid circular import
        from .annotation import Annotation

        for annotation in self.childAnnotations(study, annotatorUser=annotatorUser):
            Annotation().remove(annotation)

    def hasAnnotator(self, study, annotatorUser):
        return self.childAnnotations(study, annotatorUser=annotatorUser).count() > 0

    def addImage(self, study, image):
        # Avoid circular import
        from .annotation import Annotation

        for annotatorUser in self.getAnnotators(study):
            Annotation().createAnnotation(study, image, annotatorUser)

    def removeImage(self, study, image):
        # Avoid circular import
        from .annotation import Annotation

        for annotation in self.childAnnotations(study, image=image):
            Annotation().remove(annotation)

    def hasImage(self, study, image):
        return self.childAnnotations(study, image=image).count() > 0

    def getAnnotators(self, study):
        userIds = self.childAnnotations(study).distinct('userId')
        return User().find({
            '_id': {'$in': userIds}
        })

    def getImages(self, study):
        imageIds = self.childAnnotations(study).distinct('imageId')
        return Image().find({'_id': {'$in': imageIds}})

    def addParticipationRequest(self, study, user):
        """Add a request from a user to participate in the study."""
        self.update(
            {'_id': study['_id']},
            {'$addToSet': {'meta.participationRequests': user['_id']}}
        )

    def removeParticipationRequest(self, study, user):
        """Remove a request from a user to participate in the study."""
        if user['_id'] in study['meta']['participationRequests']:
            # The update query is a no-op if the value isn't found, but there's no reason to run it
            # unless necessary
            self.update(
                {'_id': study['_id']},
                {'$pull': {'meta.participationRequests': user['_id']}}
            )
            study['meta']['participationRequests'].remove(user['_id'])
        return study

    def hasParticipationRequest(self, study, user):
        """Check whether a user requested to participate in the study."""
        participationRequests = study['meta']['participationRequests']
        return user['_id'] in participationRequests

    def participationRequests(self, study):
        """Get the list of users requesting to participate in the study."""
        return User().find({
            '_id': {'$in': study['meta']['participationRequests']}
        })

    def childAnnotations(self, study=None, annotatorUser=None,
                         image=None, state=None, **kwargs):
        # Avoid circular import
        from .annotation import Annotation

        query = {}
        if study:
            query['studyId'] = study['_id']
        if annotatorUser:
            query['userId'] = annotatorUser['_id']
        if image:
            query['imageId'] = image['_id']
        if state:
            if state == self.State.ACTIVE:
                query['stopTime'] = None
            elif state == self.State.COMPLETE:
                query['stopTime'] = {'$ne': None}
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
                '_id': {'$in': annotations.distinct('studyId')}
            })
        return newQuery

    def list(self, user=None, limit=0, offset=0, sort=None):
        """Return a paginated list of studies that a user may access."""
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

        # Get list of users sorted by name
        def getSortedUserList(users):
            return sorted(
                (
                    User().filterSummary(studyUser, user)
                    for studyUser in
                    users
                ),
                # Sort by the obfuscated name
                key=lambda user: user['name'])

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
            'users': getSortedUserList(self.getAnnotators(study)),
            'images': list(
                Image().filterSummary(image, user)
                for image in
                self.getImages(study).sort('name', SortDir.ASCENDING)
            ),
            'questions': study['meta']['questions'],
            'features': study['meta']['features'],
            'userCompletion': {
                str(annotatorComplete['_id']): annotatorComplete['count']
                for annotatorComplete in
                Annotation().collection.aggregate([
                    {'$match': {
                        'studyId': study['_id'],
                    }},
                    {'$group': {
                        '_id': '$userId',
                        'count': {'$sum': {'$cond': {
                            'if': '$stopTime',
                            'then': 1,
                            'else': 0
                        }}}
                    }}
                ])
            }
        }

        if User().canAdminStudy(user):
            participationRequests = self.participationRequests(study)
            output['participationRequests'] = getSortedUserList(participationRequests)

        return output

    def filterSummary(self, study, user=None):
        return {
            '_id': study['_id'],
            'name': study['name'],
            'description': study['description'],
            'updated': study['updated'],
        }

    def remove(self, study):
        # Avoid circular import
        from .annotation import Annotation

        for annotation in self.childAnnotations(study):
            Annotation().remove(annotation)

        return super(Study, self).remove(study)

    def validate(self, doc, **kwargs):
        metaSchema = {
            # '$schema': 'http://json-schema.org/draft-07/schema#',
            'title': 'study.meta',
            'type': 'object',
            'properties': {
                'questions': {
                    'title': 'questions',
                    'description': 'A list of questions',
                    'type': 'array',
                    'items': {
                        'type': 'object',
                        'properties': {
                            'id': {
                                'description': 'The question text',
                                'type': 'string',
                                'minLength': 1
                            },
                            'type': {
                                'description': 'The question type',
                                'type': 'string',
                                'enum': ['select']
                            },
                            'choices': {
                                'type': 'array',
                                'items': {
                                    'description': 'A possible response value',
                                    'type': 'string',
                                    'minLength': 1
                                },
                                'minItems': 2,
                                'uniqueItems': True,
                            },
                        },
                        'required': ['id', 'type'],
                        'additionalProperties': False,
                        'anyOf': [
                            {
                                'properties': {
                                    'type': {
                                        'enum': ['select']
                                    }
                                },
                                'required': ['choices']
                            }
                            # Add validators for other types here
                        ]
                    },
                    'uniqueItems': True,
                },
                'features': {
                    'type': 'array',
                    'items': {
                        'type': 'object',
                        'properties': {
                            'id': {
                                'type': 'string',
                                'enum': MASTER_FEATURES
                            }
                        },
                        'required': ['id'],
                        'additionalProperties': False
                    },
                    'uniqueItems': True,
                },
                'participationRequests': {
                    'type': 'array',
                    'items': {
                        # TODO: each is an ObjectId for a user
                    },
                    'uniqueItems': True,
                },
            },
            'required': ['questions', 'features', 'participationRequests'],
            'additionalProperties': False
        }
        if 'meta' in doc:
            # When first saved, the the doc does not have 'meta'
            try:
                jsonschema.validate(doc['meta'], metaSchema)
            except jsonschema.ValidationError as e:
                raise ValidationException('Invalid study: ' + e.message)

        if 'name' not in doc:
            # This is a pre-validation
            return

        # TODO: implement the remainder

        return super(Study, self).validate(doc, **kwargs)
