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

import cherrypy

from girder.api import access
from girder.api.rest import Resource, RestException
from girder.api.describe import Description, describeRoute
from girder.constants import AccessType, SortDir
from girder.models.model_base import AccessException


class TaskResource(Resource):
    def __init__(self):
        super(TaskResource, self).__init__()
        self.resourceName = 'task'

        self.route('GET', ('me', 'review'), self.getReviewTasks)
        self.route('GET', ('me', 'review', 'redirect'),
                   self.redirectReviewTask)
        self.route('GET', ('me', 'segmentation'), self.getSegmentationTasks)
        self.route('GET', ('me', 'segmentation', 'redirect'),
                   self.redirectSegmentationTask)
        self.route('GET', ('me', 'annotation'), self.getAnnotationTasks)
        self.route('GET', ('me', 'annotation', 'redirect'),
                   self.redirectAnnotationTask)

    @describeRoute(
        Description('Get the current user\'s QC review tasks.')
        .responseClass('Task')
    )
    @access.user
    def getReviewTasks(self, params):
        Collection = self.model('collection')
        Dataset = self.model('dataset', 'isic_archive')
        Folder = self.model('folder')
        Image = self.model('image', 'isic_archive')
        User = self.model('user', 'isic_archive')

        user = self.getCurrentUser()
        # TODO: remove "try" once the client doesn't always call this endpoint
        try:
            User.requireReviewDataset(user)
        except AccessException:
            return []

        results = []
        for prereviewFolder in Folder.find({
            'name': 'Pre-review',
            'baseParentId': Collection.findOne({'name': 'Lesion Images'})['_id']
        }):
            if not Folder.hasAccess(
                    prereviewFolder, user=user, level=AccessType.READ):
                continue

            count = Image.find({'folderId': prereviewFolder['_id']}).count()
            if not count:
                continue

            dataset = Dataset.load(
                prereviewFolder['parentId'],
                user=user, level=AccessType.READ, exc=False)
            if not dataset:
                # This should not typically occur
                continue

            results.append({
                'dataset': {
                    '_id': dataset['_id'],
                    'name': dataset['name'],
                },
                'count': count
            })

        results.sort(key=lambda task: task['dataset']['name'])
        return results

    @describeRoute(
        Description('Redirect to a QC review task.')
        .param('datasetId',
               'An ID for the dataset to get a QC review task for.',
               required=True)
    )
    @access.cookie
    @access.user
    def redirectReviewTask(self, params):
        Dataset = self.model('dataset', 'isic_archive')
        Folder = self.model('folder')
        Image = self.model('image', 'isic_archive')
        User = self.model('user', 'isic_archive')

        self.requireParams(['datasetId'], params)

        user = self.getCurrentUser()
        User.requireReviewDataset(user)

        dataset = Dataset.load(
            params['datasetId'], user=user, level=AccessType.READ, exc=True)

        prereviewFolder = Dataset.prereviewFolder(dataset)
        if not (prereviewFolder and Folder.hasAccess(
                prereviewFolder, user=user, level=AccessType.READ)):
            raise AccessException(
                'User does not have access to any Pre-review images for this '
                'dataset.')

        if not Image.find({'folderId': prereviewFolder['_id']}).count():
            raise RestException(
                'No Pre-review images are available for this dataset.')

        reviewUrl = '/uda/gallery#/qc/%s' % dataset['_id']
        raise cherrypy.HTTPRedirect(reviewUrl, status=307)

    def _pipeline1AllImages(self, user):
        Dataset = self.model('dataset', 'isic_archive')
        return [
            # Filter viewable images out of all items
            {'$match': {
                'folderId': {'$in': [
                    dataset['_id'] for dataset in Dataset.list(user=user)]}}}
        ]

    def _pipeline1ImagesFromDataset(self, dataset):
        return [
            # Filter only images in dataset out of all items
            {'$match': {
                'folderId': dataset['_id']}}
        ]

    def _pipeline2ImagesWithSegmentations(self):
        return [
            # Drop extra fields in images (probably not necessary)
            {'$project': {
                '_id': 1,
                'folderId': 1}},
            # Join all segmentations into images
            {'$lookup': {
                'from': 'segmentation',
                'localField': '_id',
                'foreignField': 'imageId',
                'as': 'segmentations'}},
            # Drop extra fields from embedded segmentations
            {'$project': {
                '_id': 1,
                'folderId': 1,
                'segmentations._id': 1,
                'segmentations.skill': 1}}
        ]

    def _pipeline3MissingSegmentations(self):
        return [
            # Get only images with no segmentations
            {'$match': {
                'segmentations': []}}
        ]

    def _pipeline3NoExpertSegmentations(self):
        Segmentation = self.model('segmentation', 'isic_archive')
        return [
            # Get only images with no expert segmentations
            {'$match': {
                'segmentations.skill': {'$nin': [Segmentation.Skill.EXPERT]}}}
        ]

    def _pipeline4CountImage(self):
        return [
            # Count results by dataset id
            {'$group': {
                '_id': '$folderId',
                'count': {'$sum': 1}}},
            # Join dataset details into counts
            {'$lookup': {
                'from': 'folder',
                'localField': '_id',
                'foreignField': '_id',
                'as': 'dataset'}},
            # Drop extra dataset details
            {'$project': {
                '_id': 0,
                'dataset._id': 1,
                'dataset.name': 1,
                'count': 1}},
            # Flatten dataset array (which is always 1 element)
            {'$unwind': {
                'path': '$dataset'}},
            # Sort results by dataset name
            {'$sort': {
                'dataset.name': SortDir.ASCENDING}}
        ]

    def _pipeline4RandomImage(self):
        return [
            # Get a random image
            {'$sample': {
                'size': 1}},
            # Drop segmentation fields
            {'$project': {
                '_id': 1}}
        ]

    @describeRoute(
        Description('Get the current user\'s segmentation tasks.')
        .responseClass('Task')
    )
    @access.user
    def getSegmentationTasks(self, params):
        Image = self.model('image', 'isic_archive')
        Segmentation = self.model('segmentation', 'isic_archive')
        User = self.model('user', 'isic_archive')

        user = self.getCurrentUser()
        userSkill = User.getSegmentationSkill(user)
        if userSkill == Segmentation.Skill.EXPERT:
            pipeline = \
                self._pipeline1AllImages(user) + \
                self._pipeline2ImagesWithSegmentations() + \
                self._pipeline3NoExpertSegmentations() + \
                self._pipeline4CountImage()
        elif userSkill == Segmentation.Skill.NOVICE:
            pipeline = \
                self._pipeline1AllImages(user) + \
                self._pipeline2ImagesWithSegmentations() + \
                self._pipeline3MissingSegmentations() + \
                self._pipeline4CountImage()
        else:  # userSkill is None
            return []
            # TODO: raise this once the client doesn't always call this endpoint
            # raise AccessException(
            #     'You are not authorized to perform segmentations.')

        results = list(Image.collection.aggregate(pipeline))
        return results

    @describeRoute(
        Description('Redirect to a random segmentation task.')
        .param('datasetId',
               'An ID for the dataset to get a segmentation task for.',
               required=True)
    )
    @access.cookie
    @access.user
    def redirectSegmentationTask(self, params):
        Dataset = self.model('dataset', 'isic_archive')
        Image = self.model('image', 'isic_archive')
        Segmentation = self.model('segmentation', 'isic_archive')
        User = self.model('user', 'isic_archive')

        self.requireParams(['datasetId'], params)
        user = self.getCurrentUser()

        dataset = Dataset.load(
            params['datasetId'], user=user, level=AccessType.READ, exc=True)

        userSkill = User.getSegmentationSkill(user)
        if userSkill == Segmentation.Skill.EXPERT:
            # TODO: prefer an image with a novice segmentation to one with
            # no segmentations
            pipeline = \
                self._pipeline1ImagesFromDataset(dataset) + \
                self._pipeline2ImagesWithSegmentations() + \
                self._pipeline3NoExpertSegmentations() + \
                self._pipeline4RandomImage()
        elif userSkill == Segmentation.Skill.NOVICE:
            pipeline = \
                self._pipeline1ImagesFromDataset(dataset) + \
                self._pipeline2ImagesWithSegmentations() + \
                self._pipeline3MissingSegmentations() + \
                self._pipeline4RandomImage()
        else:  # userSkill is None
            raise AccessException(
                'You are not authorized to perform segmentations.')

        results = list(Image.collection.aggregate(pipeline))
        if not results:
            raise RestException('No segmentations are needed for this dataset.')
        imageId = results[0]['_id']

        segmentUrl = '/uda/segment#/%s' % imageId
        raise cherrypy.HTTPRedirect(segmentUrl, status=307)

    @describeRoute(
        Description('Get the current user\'s annotation tasks.')
        .responseClass('Task')
    )
    @access.user
    def getAnnotationTasks(self, params):
        Study = self.model('study', 'isic_archive')

        user = self.getCurrentUser()
        # TODO: this could be done more efficiently, without duplicate queries
        results = [
            {
                'study': {
                    '_id': study['_id'],
                    'name': study['name'],
                },
                'count': Study.childAnnotations(
                    study=study,
                    annotatorUser=user,
                    state=Study.State.ACTIVE
                ).count(),
            }
            for study in
            Study.find(
                annotatorUser=user,
                state=Study.State.ACTIVE,
                sort=[('lowerName', SortDir.ASCENDING)]
            )
        ]
        return results

    @describeRoute(
        Description('Redirect to the next annotation task.')
        .param('studyId',
               'An ID for the study to get an annotation task for.',
               required=True)
    )
    @access.cookie
    @access.user
    def redirectAnnotationTask(self, params):
        Study = self.model('study', 'isic_archive')

        self.requireParams(['studyId'], params)
        user = self.getCurrentUser()

        study = Study.load(
            params['studyId'], user=user, level=AccessType.READ, exc=True)
        try:
            activeAnnotations = Study.childAnnotations(
                study=study,
                annotatorUser=user,
                state=Study.State.ACTIVE,
                limit=1,
                sort=[('lowerName', SortDir.ASCENDING)]
            )
            nextAnnotation = activeAnnotations.next()
        except StopIteration:
            raise RestException('No annotations are needed for this study.')

        annotationUrl = '/uda/annotate#/%s' % nextAnnotation['_id']
        raise cherrypy.HTTPRedirect(annotationUrl, status=307)
