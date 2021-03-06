import numpy

from girder.api import access
from girder.api.describe import describeRoute, Description
from girder.api.rest import loadmodel, setRawResponse, setResponseHeader
from girder.constants import AccessType
from girder.exceptions import RestException, ValidationException
from girder.models.file import File

from .base import IsicResource
from ..models.annotation import Annotation
from ..models.image import Image
from ..models.segmentation_helpers import ScikitSegmentationHelper
from ..models.study import Study
from ..models.user import User


class AnnotationResource(IsicResource):
    def __init__(self):
        super(AnnotationResource, self).__init__()
        self.resourceName = 'annotation'

        self.route('GET', (), self.find)
        self.route('GET', (':annotationId',), self.getAnnotation)
        self.route('GET', (':annotationId', 'markup', ':featureId'),
                   self.getAnnotationMarkupMask)
        self.route('GET', (':annotationId', 'markup', ':featureId', 'rendered'),
                   self.getAnnotationMarkupRendered)
        self.route('GET', (':annotationId', 'markup', ':featureId', 'superpixels'),
                   self.getAnnotationMarkupSuperpixels)

        # TODO: These are all deprecated
        self.route('GET', (':annotationId', ':featureId'),
                   self.getAnnotationMarkupSuperpixels)
        self.route('GET', (':annotationId', ':featureId', 'mask'),
                   self.getAnnotationMarkupMask)
        self.route('GET', (':annotationId', ':featureId', 'render'),
                   self.getAnnotationMarkupRendered)

    @describeRoute(
        Description('Return a list of annotations.')
        .param('studyId', 'The ID of the study to filter by.', paramType='query', required=True)
        .param('userId', 'The ID of the user to filter by.', paramType='query', required=False)
        .param('imageId', 'The ID of the image to filter by.', paramType='query', required=False)
        .param('state', 'Filter annotations to those at a given state.', paramType='query',
               required=False, enum=('active', 'complete'))
        .param('detail', 'Display the full information for each annotation, instead of a summary.',
               required=False, dataType='boolean', default=False)
        .errorResponse()
    )
    @access.public(cookie=True)
    def find(self, params):
        self.requireParams(['studyId'], params)

        # check access here for simplicity
        study = Study().load(
            params['studyId'], user=self.getCurrentUser(),
            level=AccessType.READ, exc=True)

        annotatorUser = User().load(
            params['userId'], force=True, exc=True) \
            if 'userId' in params else None

        image = Image().load(
            params['imageId'], force=True, exc=True) \
            if 'imageId' in params else None

        state = None
        if 'state' in params:
            state = params['state']
            if state not in {Study().State.ACTIVE, Study().State.COMPLETE}:
                raise ValidationException('Value may only be "active" or "complete".', 'state')

        detail = self.boolParam('detail', params, default=False)
        filterFunc = Annotation().filter if detail else Annotation().filterSummary

        # TODO: add limit, offset, sort
        return [
            filterFunc(annotation)
            for annotation in
            Study().childAnnotations(
                study=study,
                annotatorUser=annotatorUser,
                image=image,
                state=state
            )
        ]

    @describeRoute(
        Description('Get annotation details.')
        .param('annotationId', 'The ID of the annotation to be fetched.', paramType='path')
        .errorResponse()
    )
    @access.public(cookie=True)
    @loadmodel(map={'annotationId': 'annotation'}, model='annotation', plugin='isic_archive',
               level=AccessType.READ)
    def getAnnotation(self, annotation, params):
        user = self.getCurrentUser()
        return Annotation().filter(annotation, user)

    def _ensureMarkup(self, annotation, featureId):
        # Validate pre-conditions for getting markup
        if Annotation().getState(annotation) != Study().State.COMPLETE:
            raise RestException('Annotation is incomplete.')

        study = Study().load(annotation['studyId'], force=True, exc=True)

        if not any(featureId == feature['id'] for feature in study['meta']['features']):
            raise RestException('That featureId is not present in the study.', 'featureId')
        if Annotation().getState(annotation) != Study().State.COMPLETE:
            raise RestException('Only complete annotations have markup.')

    @describeRoute(
        Description("Return an annotation's markup as a raw superpixel array.")
        .param('annotationId', 'The ID of the annotation.', paramType='path')
        .param('featureId', 'The feature ID for the markup.', paramType='path')
        .errorResponse()
    )
    @access.public(cookie=True)
    @loadmodel(map={'annotationId': 'annotation'}, model='annotation', plugin='isic_archive',
               level=AccessType.READ)
    def getAnnotationMarkupSuperpixels(self, annotation, featureId, params):
        self._ensureMarkup(annotation, featureId)

        markupFile = Annotation().getMarkupFile(annotation, featureId, includeSuperpixels=True)
        if markupFile:
            return markupFile['superpixels']
        else:
            image = Image().load(annotation['imageId'], force=True, exc=True)
            superpixelsData = Image().superpixelsData(image)
            maxSuperpixel = int(superpixelsData.max())

            return [0.0] * (maxSuperpixel + 1)

    @describeRoute(
        Description("Return an annotation's markup as a mask.")
        .param('annotationId', 'The ID of the annotation.', paramType='path')
        .param('featureId', 'The feature ID for the markup.', paramType='path')
        .produces('image/png')
        .errorResponse()
    )
    @access.public(cookie=True)
    @loadmodel(map={'annotationId': 'annotation'}, model='annotation', plugin='isic_archive',
               level=AccessType.READ)
    def getAnnotationMarkupMask(self, annotation, featureId, params):
        self._ensureMarkup(annotation, featureId)

        markupFile = Annotation().getMarkupFile(annotation, featureId)

        if markupFile:
            return File().download(markupFile, headers=True, contentDisposition='inline')
        else:
            image = Image().load(annotation['imageId'], force=True, exc=True)
            markupMask = numpy.zeros(
                (
                    image['meta']['acquisition']['pixelsY'],
                    image['meta']['acquisition']['pixelsX']
                ),
                dtype=numpy.uint8
            )
            markupMaskEncodedStream = ScikitSegmentationHelper.writeImage(markupMask, 'png')
            markupMaskEncodedData = markupMaskEncodedStream.getvalue()

            setRawResponse()
            setResponseHeader('Content-Type', 'image/png')
            contentName = 'annotation_%s_%s.png' % (
                annotation['_id'],
                # Rename features to ensure the file is downloadable on Windows
                featureId.replace(' : ', ' ; ').replace('/', ',')
            )
            setResponseHeader('Content-Disposition', f'inline; filename="{contentName}"')
            setResponseHeader('Content-Length', str(len(markupMaskEncodedData)))

            return markupMaskEncodedData

    @describeRoute(
        Description("Render an annotation's markup, overlaid on its image.")
        .param('annotationId', 'The ID of the annotation to be rendered.', paramType='path')
        .param('featureId', 'The feature ID for the markup.', paramType='path')
        .param('contentDisposition',
               'Specify the Content-Disposition response header disposition-type value.',
               required=False, enum=['inline', 'attachment'])
        .produces('image/jpeg')
        .errorResponse()
    )
    @access.public(cookie=True)
    @loadmodel(map={'annotationId': 'annotation'}, model='annotation', plugin='isic_archive',
               level=AccessType.READ)
    def getAnnotationMarkupRendered(self, annotation, featureId, params):
        contentDisp = params.get('contentDisposition', None)
        if contentDisp is not None and contentDisp not in {'inline', 'attachment'}:
            raise ValidationException(f'Unallowed contentDisposition type "{contentDisp}".',
                                      'contentDisposition')

        self._ensureMarkup(annotation, featureId)

        renderData = Annotation().renderMarkup(annotation, featureId)

        renderEncodedStream = ScikitSegmentationHelper.writeImage(renderData, 'jpeg')
        renderEncodedData = renderEncodedStream.getvalue()

        # Only setRawResponse now, as this handler may return a JSON error earlier
        setRawResponse()
        setResponseHeader('Content-Type', 'image/jpeg')
        contentName = 'annotation_%s_%s.jpg' % (
            annotation['_id'],
            # Rename features to ensure the file is downloadable on Windows
            featureId.replace(' : ', ' ; ').replace('/', ',')
        )
        if contentDisp == 'inline':
            setResponseHeader(
                'Content-Disposition',
                f'inline; filename="{contentName}"')
        else:
            setResponseHeader(
                'Content-Disposition',
                f'attachment; filename="{contentName}"')
        setResponseHeader('Content-Length', str(len(renderEncodedData)))

        return renderEncodedData
