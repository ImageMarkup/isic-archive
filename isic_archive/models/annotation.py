from bson import ObjectId
import jsonschema
import numpy

from girder.exceptions import ValidationException
from girder.models.file import File
from girder.models.model_base import Model
from girder.models.upload import Upload
from girder.utility.acl_mixin import AccessControlMixin

from .image import Image
from .segmentation_helpers import ScikitSegmentationHelper
from .study import Study
from .user import User


class Annotation(AccessControlMixin, Model):
    def initialize(self):
        self.name = 'annotation'
        self.ensureIndices(['studyId', 'imageId', 'userId'])

        # TODO: resourceColl should be ['study', 'isic_archive'], but upstream support is unclear
        self.resourceColl = 'folder'
        self.resourceParent = 'studyId'

    def createAnnotation(self, study, image, user):
        annotation = self.save({
            'studyId': study['_id'],
            'imageId': image['_id'],
            'userId': user['_id'],
            'startTime': None,
            'stopTime': None,
            'status': None,
            'log': [],
            'responses': {},
            'markups': {},
        })

        return annotation

    def getState(self, annotation):
        return (Study().State.COMPLETE
                if annotation['stopTime'] is not None
                else Study().State.ACTIVE)

    def _superpixelsToMasks(self, superpixelValues, image):
        possibleSuperpixelNums = numpy.array([
            superpixelNum
            for superpixelNum, featureValue
            in enumerate(superpixelValues)
            if featureValue == 0.5
        ])
        definiteSuperpixelNums = numpy.array([
            superpixelNum
            for superpixelNum, featureValue
            in enumerate(superpixelValues)
            if featureValue == 1.0
        ])

        superpixelsLabelData = Image().superpixelsData(image)

        possibleMask = numpy.in1d(
            superpixelsLabelData.flat,
            possibleSuperpixelNums
        ).reshape(superpixelsLabelData.shape)
        possibleMask = possibleMask.astype(numpy.bool_)
        definiteMask = numpy.in1d(
            superpixelsLabelData.flat,
            definiteSuperpixelNums
        ).reshape(superpixelsLabelData.shape)
        definiteMask = definiteMask.astype(numpy.bool_)

        return possibleMask, definiteMask

    def _superpixelsToMaskMarkup(self, superpixelValues, image):
        possibleMask, definiteMask = self._superpixelsToMasks(superpixelValues, image)

        markupMask = numpy.zeros(possibleMask.shape, dtype=numpy.uint8)
        markupMask[possibleMask] = 128
        markupMask[definiteMask] = 255

        return markupMask

    def saveSuperpixelMarkup(self, annotation, featureId, superpixelValues):
        image = Image().load(annotation['imageId'], force=True, exc=True)
        annotator = User().load(annotation['userId'], force=True, exc=True)

        markupMask = self._superpixelsToMaskMarkup(superpixelValues, image)
        markupMaskEncodedStream = ScikitSegmentationHelper.writeImage(markupMask, 'png')

        markupFile = Upload().uploadFromFile(
            obj=markupMaskEncodedStream,
            size=len(markupMaskEncodedStream.getvalue()),
            name='annotation_%s_%s.png' % (
                annotation['_id'],
                # Rename features to ensure the file is downloadable on Windows
                featureId.replace(' : ', ' ; ').replace('/', ',')
            ),
            # TODO: change this once a bug in upstream Girder is fixed
            parentType='annotation',
            parent=annotation,
            attachParent=True,
            user=annotator,
            mimeType='image/png'
        )
        markupFile['superpixels'] = superpixelValues
        # TODO: remove this once a bug in upstream Girder is fixed
        markupFile['attachedToType'] = ['annotation', 'isic_archive']
        markupFile = File().save(markupFile)

        annotation['markups'][featureId] = {
            'fileId': markupFile['_id'],
            'present': bool(markupMask.any())
        }
        return Annotation().save(annotation)

    def getMarkupFile(self, annotation, featureId, includeSuperpixels=False):
        if featureId in annotation['markups']:
            markupFile = File().load(
                annotation['markups'][featureId]['fileId'],
                force=True,
                exc=True,
                fields={'superpixels': includeSuperpixels}
            )
            return markupFile
        else:
            return None

    def renderMarkup(self, annotation, featureId):
        image = Image().load(annotation['imageId'], force=True, exc=True)
        renderData = Image().imageData(image)

        markupFile = Annotation().getMarkupFile(annotation, featureId)
        if markupFile:
            markupMask = Image()._decodeDataFromFile(markupFile)
        else:
            image = Image().load(annotation['imageId'], force=True, exc=True)
            markupMask = numpy.zeros(
                (
                    image['meta']['acquisition']['pixelsY'],
                    image['meta']['acquisition']['pixelsX']
                ),
                dtype=numpy.uint8
            )

        possibleMask = markupMask == 128
        definiteMask = markupMask == 255

        POSSIBLE_OVERLAY_COLOR = numpy.array([250, 250, 0])
        DEFINITE_OVERLAY_COLOR = numpy.array([0, 0, 255])

        renderData[possibleMask] = POSSIBLE_OVERLAY_COLOR
        renderData[definiteMask] = DEFINITE_OVERLAY_COLOR

        return renderData

    def filter(self, annotation, user=None, additionalKeys=None):
        output = {
            '_id': annotation['_id'],
            '_modelType': 'annotation',
            'studyId': annotation['studyId'],
            'image': Image().filterSummary(
                Image().load(annotation['imageId'], force=True, exc=True),
                user),
            'user': User().filterSummary(
                user=User().load(annotation['userId'], force=True, exc=True),
                accessorUser=user),
            'state': Annotation().getState(annotation)
        }
        if Annotation().getState(annotation) == Study().State.COMPLETE:
            output.update({
                'status': annotation['status'],
                'startTime': annotation['startTime'],
                'stopTime': annotation['stopTime'],
                'responses': annotation['responses'],
                'markups': {
                    featureId: markup['present']
                    for featureId, markup
                    in annotation['markups'].items()
                },
                'log': annotation.get('log', [])
            })

        return output

    def filterSummary(self, annotation, user=None):
        return {
            '_id': annotation['_id'],
            'studyId': annotation['studyId'],
            'userId': annotation['userId'],
            'imageId': annotation['imageId'],
            'state': self.getState(annotation)
        }

    def remove(self, annotation, **kwargs):
        for featureId in annotation['markups'].keys():
            File().remove(self.getMarkupFile(annotation, featureId))

        return super(Annotation, self).remove(annotation)

    def validate(self, doc):  # noqa C901
        for field in ['studyId', 'userId', 'imageId']:
            if not isinstance(doc.get(field), ObjectId):
                raise ValidationException(f'Annotation field "{field}" must be an ObjectId')

        study = Study().load(doc['studyId'], force=True, exc=False)
        if not study:
            raise ValidationException(
                'Annotation field "studyId" must reference an existing Study.')

        # If annotation is complete
        if doc.get('stopTime'):
            schema = {
                # '$schema': 'http://json-schema.org/draft-07/schema#',
                'title': 'annotation',
                'type': 'object',
                'properties': {
                    '_id': {
                        # TODO
                    },
                    'studyId': {
                        # TODO
                    },
                    'imageId': {
                        # TODO
                    },
                    'userId': {
                        # TODO
                    },
                    'startTime': {
                        # TODO
                    },
                    'stopTime': {
                        # TODO
                    },
                    'status': {
                        'type': 'string',
                        'enum': ['ok', 'phi', 'quality', 'zoom', 'inappropriate', 'other']
                    },
                    'responses': {
                        'type': 'object',
                        'properties': {
                            question['id']: {
                                'type': 'string',
                                # TODO: Support non-'select' question types
                                'enum': question['choices']
                            }
                            for question in study['meta']['questions']
                        },
                        'additionalProperties': False
                    },
                    'markups': {
                        'type': 'object',
                        'properties': {
                            feature['id']: {
                                'type': 'object',
                                'properties': {
                                    'fileId': {
                                        # TODO
                                    },
                                    'present': {
                                        'type': 'boolean'
                                    }
                                },
                                'required': ['fileId', 'present'],
                                'additionalProperties': False
                            }
                            for feature in study['meta']['features']
                        },
                        'additionalProperties': False
                    },
                    'log': {
                        # TODO
                    }
                },
                'required': [
                    '_id', 'studyId', 'imageId', 'userId', 'startTime', 'stopTime', 'status',
                    'responses', 'markups', 'log'
                ],
                'additionalProperties': False
            }
            try:
                jsonschema.validate(doc, schema)
            except jsonschema.ValidationError as e:
                raise ValidationException(f'Invalid annotation: {str(e)}')

        return doc
