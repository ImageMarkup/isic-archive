import csv
import functools
import io
import itertools

import cherrypy

from girder.api import access
from girder.api.describe import describeRoute, Description
from girder.api.rest import loadmodel, setResponseHeader
from girder.constants import AccessType, SortDir
from girder.exceptions import RestException, ValidationException
from girder.utility import mail_utils

from .base import IsicResource
from ..models.annotation import Annotation
from ..models.image import Image
from ..models.study import Study
from ..models.user import User
from ..utility import mail_utils as isic_mail_utils


class StudyResource(IsicResource):
    def __init__(self,):
        super(StudyResource, self).__init__()
        self.resourceName = 'study'

        self.route('GET', (), self.find)
        self.route('GET', (':id',), self.getStudy)
        self.route('POST', (), self.createStudy)
        self.route('POST', (':id', 'users'), self.addAnnotators)
        self.route('POST', (':id', 'images'), self.addImages)
        self.route('POST', (':id', 'participate'), self.requestToParticipate)
        self.route('DELETE', (':id',), self.deleteStudy)
        self.route('DELETE', (':id', 'users', ':userId',), self.deleteAnnotator)
        self.route('DELETE', (':id', 'participate', ':userId'), self.deleteParticipationRequest)

    @describeRoute(
        Description('Return a list of annotation studies.')
        .pagingParams(defaultSort='lowerName')
        .param('detail', 'Display the full information for each image, instead of a summary.',
               required=False, dataType='boolean', default=False)
        .param('state', 'Filter studies to those at a given state', paramType='query',
               required=False, enum=('active', 'complete'))
        .param('userId', 'Filter studies to those containing a user ID, or "me".',
               paramType='query', required=False)
        .errorResponse()
    )
    @access.public(cookie=True)
    def find(self, params):
        currentUser = self.getCurrentUser()
        detail = self.boolParam('detail', params, default=False)
        limit, offset, sort = self.getPagingParameters(params, 'lowerName')

        annotatorUser = None
        if params.get('userId'):
            if params['userId'] == 'me':
                annotatorUser = currentUser
            else:
                annotatorUser = User().load(params['userId'], force=True, exc=True)

        state = None
        if 'state' in params:
            state = params['state']
            if state not in {Study().State.ACTIVE, Study().State.COMPLETE}:
                raise ValidationException('Value may only be "active" or "complete".', 'state')

        filterFunc = Study().filter if detail else Study().filterSummary
        return [
            filterFunc(study, currentUser)
            for study in
            Study().filterResultsByPermission(
                Study().find(query=None, annotatorUser=annotatorUser, state=state, sort=sort),
                user=currentUser, level=AccessType.READ, limit=limit, offset=offset
            )
        ]

    @describeRoute(
        Description('Get a study by ID.')
        .param('id', 'The ID of the study.', paramType='path')
        .param('format', 'The output format.', paramType='query', required=False,
               enum=('csv', 'json'), default='json')
        .errorResponse()
    )
    @access.public(cookie=True)
    @loadmodel(model='study', plugin='isic_archive', level=AccessType.READ)
    def getStudy(self, study, params):
        if params.get('format') == 'csv':
            setResponseHeader('Content-Type', 'text/csv')
            setResponseHeader('Content-Disposition',
                              f'attachment; filename="{study["name"]}.csv"')
            return functools.partial(self._getStudyCSVStream, study)

        else:
            user = self.getCurrentUser()
            return Study().filter(study, user)

    def _getStudyCSVStream(self, study):
        currentUser = self.getCurrentUser()

        csvFields = tuple(itertools.chain(
            ('study_name', 'study_id',
             'user_name', 'user_id',
             'image_name', 'image_id',
             'flag_status', 'elapsed_seconds'),
            (question['id'] for question in study['meta']['questions'])
        ))

        responseBody = io.StringIO()
        csvWriter = csv.DictWriter(responseBody, csvFields, restval='')

        csvWriter.writeheader()
        yield responseBody.getvalue()
        responseBody.seek(0)
        responseBody.truncate()

        images = list(
            Study().getImages(study).sort('lowerName', SortDir.ASCENDING))

        for annotatorUser, image in itertools.product(
            sorted(
                Study().getAnnotators(study),
                key=lambda annotatorUser: User().obfuscatedName(annotatorUser)),
            images
        ):
            # this will iterate either 0 or 1 times
            for annotation in Study().childAnnotations(
                study=study,
                annotatorUser=annotatorUser,
                image=image,
                state=Study().State.COMPLETE
            ):
                elapsedSeconds = \
                    int((annotation['stopTime'] - annotation['startTime']).total_seconds())

                filteredAnnotatorUser = User().filterSummary(annotatorUser, currentUser)
                annotatorUserName = filteredAnnotatorUser['name']
                if 'login' in filteredAnnotatorUser:
                    annotatorUserName += ' [%s %s (%s)]' % (
                        filteredAnnotatorUser['firstName'],
                        filteredAnnotatorUser['lastName'],
                        filteredAnnotatorUser['login'])

                outDictBase = {
                    'study_name': study['name'],
                    'study_id': str(study['_id']),
                    'user_name': annotatorUserName,
                    'user_id': str(annotatorUser['_id']),
                    'image_name': image['name'],
                    'image_id': str(image['_id']),
                    'flag_status': annotation['status'],
                    'elapsed_seconds': elapsedSeconds
                }

                outDict = outDictBase.copy()
                for question in study['meta']['questions']:
                    if question['id'] in annotation['responses']:
                        outDict[question['id']] = annotation['responses'][question['id']]
                csvWriter.writerow(outDict)
                yield responseBody.getvalue()
                responseBody.seek(0)
                responseBody.truncate()

    @describeRoute(
        Description('Create an annotation study.')
        .param('name', 'The name of the study.', paramType='form')
        .param('userIds', 'The annotators user IDs of the study, as a JSON array.',
               paramType='form')
        .param('imageIds', 'The image IDs of the study, as a JSON array.', paramType='form')
        .param('questions', 'A list of questions for the study, as a JSON array.', paramType='form')
        .param('features', 'A list of features for the study, as a JSON array.', paramType='form')
        .errorResponse('Write access was denied on the parent folder.', 403)
    )
    @access.user
    def createStudy(self, params):
        creatorUser = self.getCurrentUser()
        User().requireAdminStudy(creatorUser)

        params = self._decodeParams(params)
        self.requireParams(['name', 'userIds', 'imageIds', 'questions', 'features'], params)

        studyName = params['name'].strip()
        if not studyName:
            raise ValidationException('Name must not be empty.', 'name')

        if not params['userIds']:
            # TODO: Remove this restriction, once users / images are not stored implicitly
            raise ValidationException('A study may not be created without users.', 'userIds')
        if len(set(params['userIds'])) != len(params['userIds']):
            raise ValidationException('Duplicate user IDs.', 'userIds')
        annotatorUsers = [
            User().load(annotatorUserId, user=creatorUser, level=AccessType.READ, exc=True)
            for annotatorUserId in params['userIds']
        ]

        if not params['imageIds']:
            # TODO: Remove this restriction, once users / images are not stored implicitly
            raise ValidationException('A study may not be created without images.', 'imageIds')
        if len(set(params['imageIds'])) != len(params['imageIds']):
            raise ValidationException('Duplicate image IDs.', 'imageIds')
        images = [
            # TODO: This should probably not allow images that the user only as access to via an
            # annotation
            Image().load(imageId, user=creatorUser, level=AccessType.READ, exc=True)
            for imageId in params['imageIds']
        ]

        try:
            study = Study().createStudy(
                name=studyName,
                creatorUser=creatorUser,
                questions=params['questions'],
                features=params['features'],
                annotatorUsers=annotatorUsers,
                images=images)
        except ValidationException as e:
            raise RestException(str(e))

        return self.getStudy(id=study['_id'], params={})

    @describeRoute(
        Description('Add annotator users to a study.')
        .param('id', 'The ID of the study.', paramType='path')
        .param('userIds', 'The user IDs to add, as a JSON array.', paramType='form')
        .errorResponse('ID was invalid.')
        .errorResponse("You don't have permission to add a study annotator.", 403)
    )
    @access.user
    @loadmodel(model='study', plugin='isic_archive', level=AccessType.READ)
    def addAnnotators(self, study, params):
        # TODO: make the loadmodel decorator use AccessType.WRITE,
        # once permissions work
        params = self._decodeParams(params)
        self.requireParams(['userIds'], params)

        creatorUser = self.getCurrentUser()
        User().requireAdminStudy(creatorUser)

        # Load all users before adding any, to ensure all are valid
        if len(set(params['userIds'])) != len(params['userIds']):
            raise ValidationException('Duplicate user IDs.', 'userIds')
        annotatorUsers = [
            User().load(userId, user=creatorUser, level=AccessType.READ, exc=True)
            for userId in params['userIds']
        ]
        duplicateAnnotations = Annotation().find({
            'studyId': study['_id'],
            'userId': {'$in': [annotatorUser['_id'] for annotatorUser in annotatorUsers]}
        })
        if duplicateAnnotations.count():
            # Just list the first duplicate
            duplicateAnnotation = next(iter(duplicateAnnotations))
            raise ValidationException(
                'Annotator user "%s" is already part of the study.' % duplicateAnnotation['userId'])
        for annotatorUser in annotatorUsers:
            study = Study().addAnnotator(study, annotatorUser)

        return self.getStudy(id=study['_id'], params={})

    @describeRoute(
        Description('Add images to a study.')
        .param('id', 'The ID of the study.', paramType='path')
        .param('imageIds', 'The image IDs to add, as a JSON array.', paramType='form')
        .errorResponse('ID was invalid.')
        .errorResponse("You don't have permission to add a study image.", 403)
    )
    @access.user
    @loadmodel(model='study', plugin='isic_archive', level=AccessType.READ)
    def addImages(self, study, params):
        params = self._decodeParams(params)
        self.requireParams(['imageIds'], params)

        creatorUser = self.getCurrentUser()
        User().requireAdminStudy(creatorUser)

        # Load all images before adding any, to ensure all are valid and
        # accessible
        if len(set(params['imageIds'])) != len(params['imageIds']):
            raise ValidationException('Duplicate image IDs.', 'imageIds')
        images = [
            # TODO: This should probably not allow images that the user only as access to via an
            # annotation
            Image().load(imageId, user=creatorUser, level=AccessType.READ, exc=True)
            for imageId in params['imageIds']
        ]
        duplicateAnnotations = Annotation().find({
            'studyId': study['_id'],
            'imageId': {'$in': [image['_id'] for image in images]}
        })
        if duplicateAnnotations.count():
            # Just list the first duplicate
            duplicateAnnotation = next(iter(duplicateAnnotations))
            raise ValidationException(
                'Image "%s" is already part of the study.' % duplicateAnnotation['imageId'])
        for image in images:
            Study().addImage(study, image)

        return self.getStudy(id=study['_id'], params={})

    @describeRoute(
        Description('Request to participate in a study.')
        .notes('Study administrators can accept the request by adding the user to the study '
               'with `POST /study/{id}/users` or delete the request with '
               '`DELETE /study/{id}/participate/{userId}`.')
        .param('id', 'The ID of the study.', paramType='path')
        .errorResponse('ID was invalid.')
    )
    @access.user
    @loadmodel(model='study', plugin='isic_archive', level=AccessType.READ)
    def requestToParticipate(self, study, params):
        currentUser = self.getCurrentUser()

        # Check if user already requested to participate in the study
        if Study().hasParticipationRequest(study, currentUser):
            raise ValidationException(
                f'User "{currentUser["_id"]}" already requested to participate in the study.')

        # Check if user is already an annotator in the study
        if Study().hasAnnotator(study, currentUser):
            raise ValidationException(f'User "{currentUser["_id"]}" is already part of the study.')

        Study().addParticipationRequest(study, currentUser)

        # Send email notification to study administrators
        host = mail_utils.getEmailUrlPrefix()
        isic_mail_utils.sendEmailToGroup(
            groupName='Study Administrators',
            templateFilename='participateInStudyRequest.mako',
            templateParams={
                'host': host,
                'study': study,
                'user': currentUser
            },
            subject='ISIC Archive: Study Participation Request')

    @describeRoute(
        Description('Delete a study.')
        .param('id', 'The ID of the study.', paramType='path')
        .errorResponse('ID was invalid.')
    )
    @access.user
    @loadmodel(model='study', plugin='isic_archive', level=AccessType.READ)
    def deleteStudy(self, study, params):
        user = self.getCurrentUser()
        # For now, study admins will be the ones that can delete studies
        User().requireAdminStudy(user)

        if Study().childAnnotations(study=study, state=Study().State.COMPLETE).count():
            raise RestException('Study has completed annotations.', 409)

        Study().remove(study)

        # No Content
        cherrypy.response.status = 204

    @describeRoute(
        Description('Delete an annotator from a study.')
        .param('id', 'The ID of the study.', paramType='path')
        .param('userId', 'The ID of the annotator.', paramType='path')
        .errorResponse('ID was invalid.')
    )
    @access.user
    @loadmodel(model='study', plugin='isic_archive', level=AccessType.READ)
    @loadmodel(model='user', plugin='isic_archive', map={'userId': 'annotatorUser'},
               level=AccessType.READ)
    def deleteAnnotator(self, study, annotatorUser, params):
        currentUser = self.getCurrentUser()
        # For now, study admins will be the ones that can delete annotators
        User().requireAdminStudy(currentUser)

        if Study().childAnnotations(
                study=study, annotatorUser=annotatorUser, state=Study().State.COMPLETE).count():
            raise RestException('Annotator user has completed annotations.', 409)

        # Check if user is already an annotator in the study
        if not Study().hasAnnotator(study, annotatorUser):
            raise ValidationException(f'User "{annotatorUser["_id"]}" is not part of the study.')

        Study().removeAnnotator(study, annotatorUser)

        # No Content
        cherrypy.response.status = 204

    @describeRoute(
        Description('Delete a request from a user to participate in a study.')
        .param('id', 'The ID of the study.', paramType='path')
        .param('userId', 'The ID of the user.', paramType='path')
        .errorResponse('ID was invalid.')
    )
    @access.user
    @loadmodel(model='study', plugin='isic_archive', level=AccessType.READ)
    @loadmodel(model='user', plugin='isic_archive', map={'userId': 'otherUser'},
               level=AccessType.READ)
    def deleteParticipationRequest(self, study, otherUser, params):
        currentUser = self.getCurrentUser()
        User().requireAdminStudy(currentUser)

        # Check if user requested to participate in the study
        if not Study().hasParticipationRequest(study, otherUser):
            raise ValidationException(
                f'User "{otherUser["_id"]}" did not request to participate in the study.')

        Study().removeParticipationRequest(study, otherUser)
