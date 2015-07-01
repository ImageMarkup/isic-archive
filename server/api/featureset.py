#!/usr/bin/env python
# -*- coding: utf-8 -*-

from girder.api import access
from girder.api.rest import Resource, loadmodel
from girder.api.describe import Description


class FeaturesetResource(Resource):
    def __init__(self,):
        self.resourceName = 'featureset'

        self.route('GET', (), self.find)
        # self.route('POST', (), self.createFeatureset)
        self.route('GET', (':id',), self.getFeatureset)
        # self.route('DELETE', (':id',), self.deleteFeatureset)


    @access.public
    def find(self, params):
        return [self.model('featureset', 'isic_archive').filter(featureset)
                for featureset in self.model('featureset', 'isic_archive').find()]
    find.description = (
        Description('List featuresets.')
        .responseClass('Featureset'))


    # @access.admin
    # def createFeatureset(self, params):
    #     # TODO: need to implement validate
    #     raise NotImplementedError()


    @access.public
    @loadmodel(model='featureset', plugin='isic_archive')
    def getFeatureset(self, featureset, params):
        return self.model('featureset', 'isic_archive').filter(featureset)
    getFeatureset.description = (
        Description('Get a featureset by ID.')
        .responseClass('Featureset')
        .param('id', 'The ID of the featureset.', paramType='path')
        .errorResponse('ID was invalid.'))


    # @access.admin
    # @loadmodel(model='featureset', plugin='isic_archive')
    # def deleteFeatureset(self, featureset, params):
    #     # TODO: need to ensure no studies are using this featureset
    #     # TODO: make this an AccessControlledModel
    #     raise NotImplementedError()
