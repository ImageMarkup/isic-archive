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

import itertools

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
        self.route('GET', ('me', 'segmentation', 'next'),
                   self.nextSegmentationTask)
        self.route('GET', ('me', 'segmentation', 'redirect'),
                   self.redirectSegmentationTask)
        self.route('GET', ('me', 'annotation'), self.getAnnotationTasks)
        self.route('GET', ('me', 'annotation', 'next'),
                   self.nextAnnotationTask)
        self.route('GET', ('me', 'annotation', 'redirect'),
                   self.redirectAnnotationTask)

    def _doRedirect(self, url):
        exc = cherrypy.HTTPRedirect(url, status=307)
        # "cherrypy.HTTPRedirect" will convert all URLs to be absolute and
        # external; however, the hostname for external URLs may not be deduced
        # correctly in all environments, so keep the url as-is
        exc.urls = [url]
        raise exc

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
        User.requireReviewDataset(user)

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
        self._doRedirect(reviewUrl)

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
                'name': 1,
                'updated': 1,
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
                'name': 1,
                'updated': 1,
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
            # Get only images with no successful expert segmentations
            {'$match': {
                'segmentations.reviews': {
                    '$not': {'$elemMatch': {
                        'skill': Segmentation.Skill.EXPERT,
                        'approved': True
                    }}
                }
            }}
        ]

    def _pipeline4CountImages(self):
        return [
            # Count results by dataset id
            {'$group': {
                '_id': '$folderId',
                'count': {'$sum': 1}}},
        ]

    def _pipeline4ListImages(self):
        return [
            # Sort images by name
            {'$sort': {
                'name': SortDir.ASCENDING}},
            # Group images by dataset id
            {'$group': {
                '_id': '$folderId',
                'images': {'$push': {
                    '_id': '$_id',
                    'name': '$name',
                    'updated': '$updated'
                }}}},
        ]

    def _pipeline5JoinDataset(self):
        return [
            # Join dataset details into groups
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
                # Note, only one of these two will actually be present
                'count': 1,
                'images': 1}},
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
                '_id': 1,
                'name': 1,
                'updated': 1}}
        ]

    @describeRoute(
        Description('Get the current user\'s segmentation tasks.')
        .responseClass('Task')
        .param('details', 'Whether a full listing of images is returned, or '
                          'just counts.', dataType='boolean', default=False)
    )
    @access.user
    def getSegmentationTasks(self, params):
        Image = self.model('image', 'isic_archive')
        Segmentation = self.model('segmentation', 'isic_archive')
        User = self.model('user', 'isic_archive')

        details = self.boolParam('details', params, False)

        user = self.getCurrentUser()
        userSkill = User.getSegmentationSkill(user)
        if userSkill is None:
            raise AccessException(
                'You are not authorized to perform segmentations.')

        pipeline = list(itertools.chain(
            self._pipeline1AllImages(user),
            self._pipeline2ImagesWithSegmentations(),
            (
                self._pipeline3NoExpertSegmentations()
                if userSkill == Segmentation.Skill.EXPERT else
                self._pipeline3MissingSegmentations()
            ),
            (
                self._pipeline4ListImages()
                if details else
                self._pipeline4CountImages()
            ),
            self._pipeline5JoinDataset()
        ))

        results = list(Image.collection.aggregate(pipeline))

        return results

    @describeRoute(
        Description('Get the next image requiring segmentation.')
        .notes('The image is selected randomly from all those requiring '
               'segmentation in the given dataset.')
        .param('datasetId', 'An ID for the dataset to filter by.',
               required=True)
    )
    @access.user
    def nextSegmentationTask(self, params):
        Dataset = self.model('dataset', 'isic_archive')
        Image = self.model('image', 'isic_archive')
        Segmentation = self.model('segmentation', 'isic_archive')
        User = self.model('user', 'isic_archive')

        self.requireParams(['datasetId'], params)
        user = self.getCurrentUser()

        dataset = Dataset.load(
            params['datasetId'], user=user, level=AccessType.READ, exc=True)

        userSkill = User.getSegmentationSkill(user)
        if userSkill is None:
            raise AccessException(
                'You are not authorized to perform segmentations.')

        pipeline = list(itertools.chain(
            self._pipeline1ImagesFromDataset(dataset),
            self._pipeline2ImagesWithSegmentations(),
            (
                # TODO: prefer an image with a novice segmentation to one with
                # no segmentations
                self._pipeline3NoExpertSegmentations()
                if userSkill == Segmentation.Skill.EXPERT else
                self._pipeline3MissingSegmentations()
            ),
            self._pipeline4RandomImage()
        ))

        results = list(Image.collection.aggregate(pipeline))
        if not results:
            raise RestException('No segmentations are needed for this dataset.')
        nextImage = results[0]

        return {
            field: nextImage[field]
            for field in
            Image.summaryFields
        }

    @describeRoute(
        Description('Redirect to a random segmentation task.')
        .param('datasetId',
               'An ID for the dataset to get a segmentation task for.',
               required=True)
    )
    @access.cookie
    @access.user
    def redirectSegmentationTask(self, params):
        nextResp = self.nextSegmentationTask(params)
        imageId = nextResp['_id']

        segmentUrl = '/uda/segment#/%s' % imageId
        self._doRedirect(segmentUrl)

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
        Description('Get the next pending annotation.')
        .param('studyId',
               'An ID for the study to get a pending annotation for.',
               required=True)
    )
    @access.user
    def nextAnnotationTask(self, params):
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
            nextAnnotation = next(iter(activeAnnotations))
        except StopIteration:
            raise RestException('No annotations are needed for this study.')

        return {
            '_id': nextAnnotation['_id'],
            'name': nextAnnotation['name'],
            'studyId': nextAnnotation['meta']['studyId'],
            'userId': nextAnnotation['meta']['userId'],
            'imageId': nextAnnotation['meta']['imageId']
        }

    @describeRoute(
        Description('Redirect to the next annotation task.')
        .param('studyId',
               'An ID for the study to get an annotation task for.',
               required=True)
    )
    @access.cookie
    @access.user
    def redirectAnnotationTask(self, params):
        nextResp = self.nextAnnotationTask(params)
        annotationId = nextResp['_id']

        annotationUrl = '/uda/annotate#/%s' % annotationId
        self._doRedirect(annotationUrl)
