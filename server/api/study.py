#!/usr/bin/env python
# -*- coding: utf-8 -*-

from girder.api import access
from girder.api.rest import Resource
from girder.api.describe import Description
from girder.constants import AccessType

from ..provision_utility import ISIC


class StudyResource(Resource):
    def __init__(self,):
        self.resourceName = 'study'

        self.route('POST', (), self.createStudy)


    @access.admin
    def createStudy(self, params):
        body_json = self.getBodyJson()

        self.requireParams(('name', 'annotatorIds', 'imageIds', 'featuresetId'), body_json)

        creator_user = self.getCurrentUser()
        annotator_users = [self.model('user').load(annotator_id, user=creator_user, level=AccessType.READ)
                           for annotator_id in body_json['annotatorIds']]
        # TODO: validate that these items are actually in the correct folder
        image_items = [self.model('item').load(image_id, user=creator_user, level=AccessType.READ)
                       for image_id in body_json['imageIds']]
        featureset_item = self.model('featureset', 'isic_archive').load(body_json['featuresetId'])

        # this may raise a ValidationException if the name already exists
        study_folder = self.model('folder').createFolder(
            parent=ISIC.AnnotationStudies.collection,
            name=body_json['name'],
            description='',
            parentType='collection',
            public=None,
            creator=creator_user
        )
        self.model('folder').copyAccessPolicies(
            src=ISIC.AnnotationStudies.collection,
            dest=study_folder,
            save=False
        )
        self.model('folder').setUserAccess(
            doc=study_folder,
            user=creator_user,
            # TODO: make admin
            level=AccessType.READ,
            save=False
        )
        # "setMetadata" will always save
        self.model('folder').setMetadata(
            folder=study_folder,
            metadata={
                'featuresetId': featureset_item['_id']
            }
        )


        for annotator_user in annotator_users:
            annotator_folder = self.model('folder').createFolder(
                parent=study_folder,
                name='%(login)s (%(firstName)s %(lastName)s)' % annotator_user,
                description='',
                parentType='folder',
                public=True,
                creator=annotator_user
            )
            # study creator accesses will already have been copied to this sub-folder
            self.model('folder').setUserAccess(
                doc=annotator_folder,
                user=annotator_user,
                # TODO: make write
                level=AccessType.READ,
                save=True
            )

            for image_item in image_items:
                annotation_item = self.model('item').createItem(
                    folder=annotator_folder,
                    name=image_item['name'],
                    description='',
                    creator=annotator_user
                )
                self.model('item').setMetadata(
                    item=annotation_item,
                    metadata={
                        'studyId': study_folder['_id'],
                        'start_time': None,
                        'stop_time': None,
                        'annotations': None,
                    }
                )
    createStudy.description = (
        Description('Create an annotation study.')
        .param('body', 'JSON containing the study parameters.', paramType='body')
        .errorResponse()
        .errorResponse('Write access was denied on the parent folder.', 403))
