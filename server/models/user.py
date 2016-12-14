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

from girder.models.user import User as UserModel
from girder.models.model_base import AccessException, ValidationException


class User(UserModel):
    def initialize(self):
        super(User, self).initialize()

        # self.summaryFields = ['_id', 'login', 'firstName', 'lastName']

    def filteredSummary(self, user, accessorUser):
        if self.hasAccess(user, accessorUser):
            return {
                field: user[field]
                for field in
                ['_id', 'login', 'firstName', 'lastName']
            }
        else:
            return {
                field: user[field]
                for field in
                ['_id', 'login']
            }

    def _isAdminOrMember(self, user, groupName):
        Group = self.model('group')
        if not user:
            return False
        if user.get('admin', False):
            return True
        group = Group.findOne({'name': groupName})
        if not group:
            raise ValidationException('Could not load group: %s' % groupName)
        return group['_id'] in user['groups']

    def canCreateDataset(self, user):
        return self._isAdminOrMember(user, 'Dataset Contributors')

    def requireCreateDataset(self, user):
        if not self.canCreateDataset(user):
            raise AccessException(
                'Only members of the Dataset Contributors group can create '
                'datasets.')

    def canReviewDataset(self, user):
        return self._isAdminOrMember(user, 'Dataset QC Reviewers')

    def requireReviewDataset(self, user):
        if not self.canReviewDataset(user):
            raise AccessException(
                'Only members of the Dataset QC Reviewers group can review '
                'datasets.')

    def getSegmentationSkill(self, user):
        Group = self.model('group')
        Segmentation = self.model('segmentation', 'isic_archive')
        if not user:
            return None
        expertGroup = Group.findOne({'name': 'Segmentation Experts'})
        if expertGroup['_id'] in user['groups']:
            return Segmentation.Skill.EXPERT
        noviceGroup = Group.findOne({'name': 'Segmentation Novices'})
        if noviceGroup['_id'] in user['groups']:
            return Segmentation.Skill.NOVICE
        return None

    def requireSegmentationSkill(self, user):
        if self.getSegmentationSkill(user) is None:
            raise AccessException(
                'Only members of the Segmentation Experts and Segmentation '
                'Novices groups can create or review segmentations.')

    def canAdminStudy(self, user):
        return self._isAdminOrMember(user, 'Study Administrators')

    def requireAdminStudy(self, user):
        if not self.canAdminStudy(user):
            raise AccessException(
                'Only members of the Study Administrators group can create or '
                'modify studies.')
