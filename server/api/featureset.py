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

from girder.api import access
from girder.api.rest import Resource, loadmodel
from girder.api.describe import Description, describeRoute


class FeaturesetResource(Resource):
    def __init__(self):
        super(FeaturesetResource, self).__init__()
        self.resourceName = 'featureset'

        self.route('GET', (), self.find)
        self.route('GET', (':id',), self.getFeatureset)

    @describeRoute(
        Description('List featuresets.')
        .pagingParams(defaultSort='name')
        .responseClass('Featureset')
    )
    @access.public
    def find(self, params):
        Featureset = self.model('featureset', 'isic_archive')

        # TODO: make the default sort lowerName (after adding that field)
        limit, offset, sort = self.getPagingParameters(params, 'name')

        return [
            {
                field: featureset[field]
                for field in
                Featureset.summaryFields
            }
            for featureset in
            Featureset.find(
                limit=limit,
                offset=offset,
                sort=sort
            )
        ]

    @describeRoute(
        Description('Get a featureset by ID.')
        .responseClass('Featureset')
        .param('id', 'The ID of the featureset.', paramType='path')
        .errorResponse('ID was invalid.')
    )
    @access.public
    @loadmodel(model='featureset', plugin='isic_archive')
    def getFeatureset(self, featureset, params):
        Featureset = self.model('featureset', 'isic_archive')
        User = self.model('user')

        output = Featureset.filter(featureset)

        userSummaryFields = ('_id', 'login', 'firstName', 'lastName')
        creator = User.load(output.pop('creatorId'), force=True)
        output['creator'] = {
            field: creator[field]
            for field in
            userSummaryFields
        }

        return output
