#!/usr/bin/env python
# -*- coding: utf-8 -*-

from girder.api import access
from girder.api.rest import Resource, loadmodel
from girder.api.describe import Description, describeRoute
from girder.constants import AccessType


class FeaturesetResource(Resource):
    def __init__(self):
        super(FeaturesetResource, self).__init__()
        self.resourceName = 'featureset'

        self.route('GET', (), self.find)
        # self.route('POST', (), self.createFeatureset)
        self.route('GET', (':id',), self.getFeatureset)
        # self.route('DELETE', (':id',), self.deleteFeatureset)


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


    # @access.admin
    # def createFeatureset(self, params):
    #     # TODO: need to implement validate
    #     raise NotImplementedError()


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
        creator = User.load(output.pop('creatorId'))
        output['creator'] = {
            field: creator[field]
            for field in
            userSummaryFields
        }

        return output


    # @access.admin
    # @loadmodel(model='featureset', plugin='isic_archive', level=AccessType.ADMIN)
    # def deleteFeatureset(self, featureset, params):
    #     # TODO: need to ensure no studies are using this featureset
    #     # TODO: make this an AccessControlledModel
    #     raise NotImplementedError()
