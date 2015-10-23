#!/usr/bin/env python
# -*- coding: utf-8 -*-

from girder.api import access
from girder.api.rest import Resource, loadmodel
from girder.api.describe import Description
from girder.constants import AccessType


class DatasetResource(Resource):
    def __init__(self,):
        self.resourceName = 'study'

        self.route('GET', (), self.find)
        self.route('GET', (':id',), self.getDataset)


    @access.public
    def find(self, params):
        limit, offset, sort = self.getPagingParameters(params, 'lowerName')

        # TODO: use a Dataset.list method to filter accesses
        return [self.model('dataset', 'isic_archive').filter(dataset, self.getCurrentUser())
                for dataset in self.model('dataset', 'isic_archive').find(
                    limit=limit, offset=offset, sort=sort)]

    find.description = (
        Description('Return a list of lesion image datasets.')
        .pagingParams(defaultSort='name')
        .errorResponse())


    @access.public
    @loadmodel(model='dataset', plugin='isic_archive', level=AccessType.READ)
    def getDataset(self, dataset, params):
        return self.model('dataset', 'isic_archive').filter(dataset, self.getCurrentUser())

    getDataset.description = (
        Description('Get a lesion image datasets by ID.')
        .param('id', 'The ID of the datasets.', paramType='path')
        .errorResponse())
