#!/usr/bin/env python
# -*- coding: utf-8 -*-

from girder.api import access
from girder.api.rest import Resource, loadmodel
from girder.api.describe import Description, describeRoute
from girder.constants import AccessType


class DatasetResource(Resource):
    def __init__(self):
        super(DatasetResource, self).__init__()
        self.resourceName = 'dataset'

        self.route('GET', (), self.find)
        self.route('GET', (':id',), self.getDataset)


    @describeRoute(
        Description('Return a list of lesion image datasets.')
        .pagingParams(defaultSort='lowerName')
        .errorResponse()
    )
    @access.public
    def find(self, params):
        limit, offset, sort = self.getPagingParameters(params, 'lowerName')

        return [
            {
                field: dataset[field]
                for field in
                self.model('dataset', 'isic_archive').summaryFields
            }
            for dataset in
            self.model('dataset', 'isic_archive').list(
                user=self.getCurrentUser(),
                limit=limit, offset=offset, sort=sort)
        ]


    @describeRoute(
        Description('Return a lesion image dataset\'s details.')
        .param('id', 'The ID of the dataset.', paramType='path')
        .errorResponse('ID was invalid.')
    )
    @access.public
    @loadmodel(model='dataset', plugin='isic_archive', level=AccessType.READ)
    def getDataset(self, dataset, params):
        return self.model('dataset', 'isic_archive').filter(
            dataset, self.getCurrentUser())
