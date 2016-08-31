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


class User(UserModel):
    def initialize(self):
        super(User, self).initialize()

        # self.summaryFields = ['_id', 'login', 'firstName', 'lastName']

    def filteredSummary(self, user, accessorUser, anonymousIndex=None):
        if accessorUser.get('admin', False):
            return {
                field: user[field]
                for field in
                ['_id', 'login', 'firstName', 'lastName']
            }
        elif anonymousIndex is not None:
            if not isinstance(anonymousIndex, int) or \
                    anonymousIndex > 25:
                raise ValueError('anonymousIndex must be an int < 26')
            anonymousLabel = chr(ord('A') + anonymousIndex)
            return {
                '_id': user['_id'],
                'login': 'Rater %s' % anonymousLabel
            }
        else:
            return {
                field: user[field]
                for field in
                ['_id', 'login']
            }
