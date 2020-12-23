import csv
import functools
import io
import itertools

from girder.api import access
from girder.api.describe import describeRoute, Description
from girder.api.rest import loadmodel, setResponseHeader
from girder.constants import AccessType, SortDir
from girder.exceptions import ValidationException

from .base import IsicResource
from ..models.study import Study
from ..models.user import User


class StudyResource(IsicResource):
    def __init__(self,):
        super(StudyResource, self).__init__()
        self.resourceName = 'study'

        self.route('GET', (), self.find)
        self.route('GET', (':id',), self.getStudy)

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
