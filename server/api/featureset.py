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
from girder.api.rest import loadmodel
from girder.api.describe import Description, describeRoute
from girder.constants import SortDir
from girder.models.model_base import ValidationException

from .base import IsicResource


class FeaturesetResource(IsicResource):
    def __init__(self):
        super(FeaturesetResource, self).__init__()
        self.resourceName = 'featureset'

        self.route('GET', (), self.find)
        self.route('GET', (':id',), self.getFeatureset)
        self.route('POST', (), self.createFeatureset)

    @describeRoute(
        Description('List featuresets.')
        .pagingParams(defaultSort='name')
        .responseClass('Featureset')
    )
    @access.cookie
    @access.public
    def find(self, params):
        Featureset = self.model('featureset', 'isic_archive')

        # TODO: make the default sort lowerName (after adding that field)
        limit, offset, sort = self.getPagingParameters(params, 'name')

        # Since names may be identical, add an additional sort field for
        # convenience, especially as the REST interface cannot specify multiple
        # fields
        if sort == [('name', SortDir.ASCENDING)]:
            sort.append(('version', SortDir.ASCENDING))
        elif sort == [('name', SortDir.DESCENDING)]:
            sort.append(('version', SortDir.DESCENDING))

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
    @access.cookie
    @access.public
    @loadmodel(model='featureset', plugin='isic_archive')
    def getFeatureset(self, featureset, params):
        Featureset = self.model('featureset', 'isic_archive')
        User = self.model('user', 'isic_archive')

        output = Featureset.filter(featureset)

        output['creator'] = User.filteredSummary(
            User.load(
                output.pop('creatorId'),
                force=True, exc=True),
            self.getCurrentUser())

        return output

    @describeRoute(
        Description('Create a featureset.')
        .param('name', 'The name of the featureset.', paramType='form')
        .param('version', 'The numeric version of the featureset.',
               paramType='form')
        .param('globalFeatures',
               'The global features of the featureset, as a JSON array.',
               paramType='form')
        .param('localFeatures',
               'The local features of the featureset, as a JSON array.',
               paramType='form')
        .errorResponse('Write access was denied on the parent folder.', 403)
    )
    @access.user
    def createFeatureset(self, params):
        Featureset = self.model('featureset', 'isic_archive')
        User = self.model('user', 'isic_archive')

        creatorUser = self.getCurrentUser()
        # For now, study admins will be the ones that can create featuresets
        User.requireAdminStudy(creatorUser)

        params = self._decodeParams(params)
        self.requireParams(
            ['name', 'version', 'globalFeatures', 'localFeatures'],
            params)

        featuresetName = params['name'].strip()
        if not featuresetName:
            raise ValidationException('Name must not be empty.', 'name')

        try:
            featuresetVersion = float(params['version'])
        except ValueError:
            raise ValidationException('Version must be a number.', 'version')

        # These will be validated once the new featureset is created
        globalFeatures = params['globalFeatures']
        localFeatures = params['localFeatures']

        featureset = Featureset.createFeatureset(
            name=featuresetName,
            version=featuresetVersion,
            creator=creatorUser,
            globalFeatures=globalFeatures,
            localFeatures=localFeatures)

        return self.getFeatureset(id=featureset['_id'], params={})
