import copy
import functools
import math
import re
from typing import Dict, List, Set, Tuple


class MetadataFieldException(Exception):
    """Base class for exceptions raised while parsing metadata fields."""

    pass


class MetadataFieldNotFoundException(MetadataFieldException):
    """Exception raised when none of the fields that a parser supports are found."""

    def __init__(self, fields):
        super(MetadataFieldNotFoundException, self).__init__()
        self.fields = fields


class MetadataValueExistsException(MetadataFieldException):
    """Exception raised when a value for a field already exists and can't be safely overwritten."""

    def __init__(self, name, oldValue, newValue):
        super(MetadataValueExistsException, self).__init__()
        self.name = name
        self.oldValue = oldValue
        self.newValue = newValue


class MultipleFieldException(MetadataFieldException):
    """Exception raised when more than one fields that a parser supports are found."""

    def __init__(self, name, fields):
        super(MultipleFieldException, self).__init__()
        self.name = name
        self.fields = fields


class BadFieldTypeException(MetadataFieldException):
    """Exception raised when the value for a field is the wrong type."""

    def __init__(self, name, fieldType, value):
        super(BadFieldTypeException, self).__init__()
        self.name = name
        self.fieldType = fieldType
        self.value = value


class InconsistentValuesException(MetadataFieldException):
    """Exception raised when the values of a group of fields don't adhere to validation rules."""

    def __init__(self, names, values):
        super(InconsistentValuesException, self).__init__()
        self.names = names
        self.values = values


class FieldParser(object):
    name = ''
    allowedFields: Set[str] = set()

    @classmethod
    def run(cls, data, acquisition, clinical, private):
        try:
            rawValue = cls.extract(data)
        except MetadataFieldNotFoundException:
            # The field doesn't exist in the given data, which is harmless
            return

        cleanValue = cls.transform(rawValue)
        cls.load(cleanValue, acquisition, clinical, private)

    @classmethod
    def extract(cls, data):
        """
        Extract the value for this parser's field.

        Field keys in data are matched case insensitively.
        A MetadataFieldNotFoundException is raised if none of the allowed fields are found.
        A MultipleFieldException is raised if more than one of the allowed fields are found.
        """
        availableFields = data.keys()
        allowedFields = set(field.lower() for field in cls.allowedFields)

        foundFields = [field for field
                       in availableFields
                       if field.lower() in allowedFields]

        if not foundFields:
            raise MetadataFieldNotFoundException(fields=cls.allowedFields)
        if len(foundFields) > 1:
            raise MultipleFieldException(name=cls.name, fields=sorted(foundFields))

        field = foundFields.pop()
        value = data.pop(field)

        if value is not None:
            value = str(value)

        assert(value is None or isinstance(value, str))

        return value

    @classmethod
    def transform(cls, value):
        """
        Implement in subclasses.

        Values that are None, match the empty string, 'unknown', or sometimes 'not applicable'
        (ignoring case) should be coerced to None.
        """
        raise NotImplementedError()

    @classmethod
    def load(cls, value, acquisition, clinical, private):
        """Implement in subclasses."""
        raise NotImplementedError()

    @classmethod
    def _coerceInt(cls, value):
        try:
            value = int(float(value))
        except ValueError:
            raise BadFieldTypeException(name=cls.name, fieldType='integer', value=value)
        return value

    @classmethod
    def _coerceFloat(cls, value):
        try:
            value = float(value)
            if math.isinf(value) or math.isnan(value):
                raise ValueError
        except ValueError:
            raise BadFieldTypeException(name=cls.name, fieldType='float', value=value)
        return value

    @classmethod
    def _coerceBool(cls, value):
        if value in ['true', 'yes']:
            return True
        elif value in ['false', 'no']:
            return False
        else:
            raise BadFieldTypeException(name=cls.name, fieldType='boolean', value=value)

    @classmethod
    def _assertEnumerated(cls, value, allowed):
        if value not in allowed:
            expected = f'one of {str(sorted(allowed))}'
            raise BadFieldTypeException(name=cls.name, fieldType=expected, value=value)

    @classmethod
    def _checkWrite(cls, metadata, key, value):
        """
        Check that the value for the key can safely be written.

        The following scenarios allow writes:
        - the old value doesn't exist in the metadata dictionary
        - the old value is None
        - the old value matches the new value

        Otherwise, a MetadataValueExistsException is raised.
        """
        oldValue = metadata.get(key)
        if (oldValue is not None) and (oldValue != value):
            raise MetadataValueExistsException(name=key, oldValue=oldValue, newValue=value)


class AgeFieldParser(FieldParser):
    name = 'age'
    approxName = 'age_approx'
    allowedFields = {'age'}

    @classmethod
    def transform(cls, value):
        if value is not None:
            value = value.strip()
            value = value.lower()
            if value in ['', 'unknown']:
                value = None
            else:
                if value == '85+':
                    value = '85'
                value = cls._coerceInt(value)
                if value > 85:
                    value = 85
        return value

    @classmethod
    def load(cls, value, acquisition, clinical, private):
        approxAge = \
            int(round(value / 5.0) * 5) \
            if value is not None \
            else None

        cls._checkWrite(private, cls.name, value)
        cls._checkWrite(clinical, cls.approxName, approxAge)

        private[cls.name] = value
        clinical[cls.approxName] = approxAge


class SexFieldParser(FieldParser):
    name = 'sex'
    allowedFields = {'sex', 'gender'}

    @classmethod
    def transform(cls, value):
        if value is not None:
            value = value.strip()
            value = value.lower()
            if value in ['', 'unknown']:
                value = None
            else:
                if value == 'm':
                    value = 'male'
                elif value == 'f':
                    value = 'female'
                cls._assertEnumerated(value, {'male', 'female'})
        return value

    @classmethod
    def load(cls, value, acquisition, clinical, private):
        cls._checkWrite(clinical, cls.name, value)
        clinical[cls.name] = value


class HxMmFieldParser(FieldParser):
    @classmethod
    def transform(cls, value):
        if value is not None:
            value = value.strip()
            value = value.lower()
            if value in ['', 'unknown']:
                value = None
            else:
                value = cls._coerceBool(value)
        return value

    @classmethod
    def load(cls, value, acquisition, clinical, private):
        cls._checkWrite(clinical, cls.name, value)
        clinical[cls.name] = value


class FamilyHxMmFieldParser(HxMmFieldParser):
    name = 'family_hx_mm'
    allowedFields = {'family_hx_mm', 'FamHxMM'}


class PersonalHxMmFieldParser(HxMmFieldParser):
    name = 'personal_hx_mm'
    allowedFields = {'personal_hx_mm'}


class ClinicalSizeFieldParser(FieldParser):
    """
    Parse clinical size field.

    Expects units to be specified (um, mm, or cm).
    """

    name = 'clin_size_long_diam_mm'
    allowedFields = {'clin_size_long_diam_mm'}
    _formatRegex = re.compile(r'(.+)(um|mm|cm)$')

    @classmethod
    def transform(cls, value):
        if value is not None:
            value = value.strip()
            value = value.lower()
            if value in ['', 'unknown']:
                value = None
            else:
                def raiseBadFieldTypeExceptionWithValue(value):
                    raise BadFieldTypeException(
                        name=cls.name, fieldType='float with units (um, mm, or cm)', value=value)

                raiseBadFieldTypeException = functools.partial(
                    raiseBadFieldTypeExceptionWithValue, value)

                # Parse value into floating point component and units
                result = re.match(cls._formatRegex, value)
                if not result:
                    raiseBadFieldTypeException()

                try:
                    value, units = result.groups()
                    value = cls._coerceFloat(value)
                except BadFieldTypeException:
                    raiseBadFieldTypeException()

                # Convert to mm
                if units == 'um':
                    value *= 1e-3
                elif units == 'cm':
                    value *= 1e1

        return value

    @classmethod
    def load(cls, value, acquisition, clinical, private):
        cls._checkWrite(clinical, cls.name, value)
        clinical[cls.name] = value


class MelanocyticFieldParser(FieldParser):
    name = 'melanocytic'
    allowedFields = {'melanocytic'}
    melanocyticDiagnoses = [
        'AIMP',
        'melanoma',
        'melanoma metastasis',
        'nevus',
        'nevus spilus',
        'atypical melanocytic proliferation',
        'lentigo simplex',
        'lentigo NOS',
    ]

    @classmethod
    def transform(cls, value):
        if value is not None:
            value = value.strip()
            value = value.lower()
            if value in ['', 'unknown']:
                value = None
            else:
                value = cls._coerceBool(value)
        return value

    @classmethod
    def load(cls, value, acquisition, clinical, private):
        cls._checkWrite(clinical, cls.name, value)
        clinical[cls.name] = value


class DiagnosisConfirmTypeFieldParser(FieldParser):
    name = 'diagnosis_confirm_type'
    allowedFields = {'diagnosis_confirm_type'}

    @classmethod
    def transform(cls, value):
        if value is not None:
            value = value.strip()
            value = value.lower()
            if value in ['', 'unknown']:
                value = None
            else:
                cls._assertEnumerated(value, {
                    'histopathology',
                    'serial imaging showing no change',
                    'single image expert consensus',
                    'confocal microscopy with consensus dermoscopy'})
        return value

    @classmethod
    def load(cls, value, acquisition, clinical, private):
        cls._checkWrite(clinical, cls.name, value)
        clinical[cls.name] = value


class BenignMalignantFieldParser(FieldParser):
    name = 'benign_malignant'
    allowedFields = {'benign_malignant', 'ben_mal'}

    @classmethod
    def transform(cls, value):
        if value is not None:
            value = value.strip()
            value = value.lower()
            if value in ['', 'unknown']:
                value = None
            else:
                if value == 'indeterminable':
                    value = 'indeterminate'
                cls._assertEnumerated(value, {
                    'benign',
                    'malignant',
                    'indeterminate',
                    'indeterminate/benign',
                    'indeterminate/malignant'})
        return value

    @classmethod
    def load(cls, value, acquisition, clinical, private):
        cls._checkWrite(clinical, cls.name, value)
        clinical[cls.name] = value

#
# if 'diagnosis_confirm_type' not in clinical:
#             # TODO: remove this, it's always going to be there
#             raise Exception('"diagnosis_confirm_type" must also be set')
#
#         if value in {'malignant', 'indeterminate/malignant'}:
#             if clinical['diagnosis_confirm_type'] != 'histopathology':
#                 raise Exception(
#                     'if this value is "malignant", "diagnosis_confirm_type" '
#                     'must be "histopathology"')


class DiagnosisFieldParser(FieldParser):
    name = 'diagnosis'
    allowedFields = {'diagnosis', 'path_diagnosis'}

    @classmethod
    def transform(cls, value):
        if value is not None:
            value = value.strip()
            value = value.lower()
            if value in ['', 'unknown']:
                value = None
            else:
                if value == 'aimp':
                    value = 'AIMP'
                elif value == 'lentigo nos':
                    value = 'lentigo NOS'
                elif value == 'caf\xe9-au-lait macule':
                    # Deal with a possible unicode char in "cafe-au-lait macule"
                    # TODO: instead, actually use the unicode char here
                    value = 'cafe-au-lait macule'
                cls._assertEnumerated(value, {
                    'actinic keratosis',
                    'adnexal tumor',
                    'AIMP',
                    'angiokeratoma',
                    'angioma',
                    'basal cell carcinoma',
                    'cafe-au-lait macule',
                    'dermatofibroma',
                    'ephelis',
                    'lentigo NOS',
                    'lentigo simplex',
                    'lichenoid keratosis',
                    'melanoma',
                    'melanoma metastasis',
                    'merkel cell carcinoma',
                    'mucosal melanosis',
                    'nevus',
                    'nevus spilus',
                    'seborrheic keratosis',
                    'solar lentigo',
                    'squamous cell carcinoma',
                    'clear cell acanthoma',
                    'atypical spitz tumor',
                    'acrochordon',
                    'angiofibroma or fibrous papule',
                    'neurofibroma',
                    'pyogenic granuloma',
                    'scar',
                    'sebaceous adenoma',
                    'sebaceous hyperplasia',
                    'verruca',
                    'atypical melanocytic proliferation',
                    'epidermal nevus',
                    'pigmented benign keratosis',
                    'vascular lesion',
                    'other'})
        return value

    @classmethod
    def load(cls, value, acquisition, clinical, private):
        cls._checkWrite(clinical, cls.name, value)
        clinical[cls.name] = value


class NevusTypeFieldParser(FieldParser):
    name = 'nevus_type'
    allowedFields = {'nevus_type'}

    @classmethod
    def transform(cls, value):
        if value is not None:
            value = value.strip()
            value = value.lower()
            if value in ['', 'unknown', 'not applicable']:
                value = None
            else:
                if value == 'nevus nos':
                    value = 'nevus NOS'
                cls._assertEnumerated(value, {
                    'blue',
                    'combined',
                    'nevus NOS',
                    'deep penetrating',
                    'halo',
                    'persistent/recurrent',
                    'pigmented spindle cell of reed',
                    'plexiform spindle cell',
                    'special site',
                    'spitz'})
        return value

    @classmethod
    def load(cls, value, acquisition, clinical, private):
        cls._checkWrite(clinical, cls.name, value)
        clinical[cls.name] = value


class ImageTypeFieldParser(FieldParser):
    name = 'image_type'
    allowedFields = {'image_type'}

    @classmethod
    def transform(cls, value):
        if value is not None:
            value = value.strip()
            value = value.lower()
            if value in ['', 'unknown']:
                value = None
            else:
                cls._assertEnumerated(value, {
                    'dermoscopic',
                    'clinical',
                    'overview'})
        return value

    @classmethod
    def load(cls, value, acquisition, clinical, private):
        cls._checkWrite(acquisition, cls.name, value)
        acquisition[cls.name] = value


class DermoscopicTypeFieldParser(FieldParser):
    name = 'dermoscopic_type'
    allowedFields = {'dermoscopic_type', 'dermoscopy_type'}

    @classmethod
    def transform(cls, value):
        if value is not None:
            value = value.strip()
            value = value.lower()
            if value in ['', 'unknown', 'not applicable']:
                value = None
            else:
                if value == 'contact non polarized':
                    value = 'contact non-polarized'
                elif value == 'non contact polarized':
                    value = 'non-contact polarized'
                cls._assertEnumerated(value, {
                    'contact polarized',
                    'contact non-polarized',
                    'non-contact polarized'})
        return value

    @classmethod
    def load(cls, value, acquisition, clinical, private):
        cls._checkWrite(acquisition, cls.name, value)
        acquisition[cls.name] = value


class MelThickMmFieldParser(FieldParser):
    name = 'mel_thick_mm'
    allowedFields = {'mel_thick_mm', 'mel_thick'}
    _formatRegex = re.compile(r"""
        (.+?)    # Non-greedy
        (?:mm)?  # Optional units, non-capturing
        $
        """, re.VERBOSE)

    @classmethod
    def transform(cls, value):
        if value is not None:
            value = value.strip()
            value = value.lower()
            if value in ['', 'unknown', 'not applicable']:
                value = None
            else:
                def raiseBadFieldTypeExceptionWithValue(value):
                    raise BadFieldTypeException(
                        name=cls.name, fieldType='float with optional units (mm)', value=value)

                raiseBadFieldTypeException = functools.partial(
                    raiseBadFieldTypeExceptionWithValue, value)

                # Parse value into floating point component and units
                result = re.match(cls._formatRegex, value)
                if not result:
                    raiseBadFieldTypeException()

                try:
                    value = result.group(1)
                    value = cls._coerceFloat(value)
                except BadFieldTypeException:
                    raiseBadFieldTypeException()

        return value

    @classmethod
    def load(cls, value, acquisition, clinical, private):
        cls._checkWrite(clinical, cls.name, value)
        clinical[cls.name] = value


class MelClassFieldParser(FieldParser):
    name = 'mel_class'
    allowedFields = {'mel_class'}

    @classmethod
    def transform(cls, value):
        if value is not None:
            value = value.strip()
            value = value.lower()
            if value in ['', 'unknown', 'not applicable']:
                value = None
            else:
                if value == 'recurrent/persistent melanoma in situ':
                    value = 'recurrent/persistent melanoma, in situ'
                elif value == 'recurrent/persistent melanoma invasive':
                    value = 'recurrent/persistent melanoma, invasive'
                elif value == 'melanoma nos':
                    value = 'melanoma NOS'
                cls._assertEnumerated(value, {
                    'melanoma in situ',
                    'invasive melanoma',
                    'recurrent/persistent melanoma, in situ',
                    'recurrent/persistent melanoma, invasive',
                    'melanoma NOS'})
        return value

    @classmethod
    def load(cls, value, acquisition, clinical, private):
        cls._checkWrite(clinical, cls.name, value)
        clinical[cls.name] = value


class MelTypeFieldParser(FieldParser):
    name = 'mel_type'
    allowedFields = {'mel_type'}

    @classmethod
    def transform(cls, value):
        if value is not None:
            value = value.strip()
            value = value.lower()
            if value in ['', 'unknown', 'not applicable']:
                value = None
            else:
                if value == 'ssm':
                    value = 'superficial spreading melanoma'
                elif value == 'lmm':
                    value = 'lentigo maligna melanoma'
                elif value == 'alm':
                    value = 'acral lentiginous melanoma'
                elif value == 'melanoma nos':
                    value = 'melanoma NOS'
                cls._assertEnumerated(value, {
                    'superficial spreading melanoma',
                    'nodular melanoma',
                    'lentigo maligna melanoma',
                    'acral lentiginous melanoma',
                    'melanoma NOS'})
        return value

    @classmethod
    def load(cls, value, acquisition, clinical, private):
        cls._checkWrite(clinical, cls.name, value)
        clinical[cls.name] = value


class MelMitoticIndexFieldParser(FieldParser):
    name = 'mel_mitotic_index'
    allowedFields = {'mel_mitotic_index', 'mel_mit'}

    @classmethod
    def transform(cls, value):
        if value is not None:
            value = value.strip()
            value = value.lower()
            if value in ['', 'unknown', 'not applicable']:
                value = None
            else:
                value = re.sub(r'mm2$', 'mm^2', value)
                cls._assertEnumerated(value, {
                    '0/mm^2',
                    '<1/mm^2',
                    '1/mm^2',
                    '2/mm^2',
                    '3/mm^2',
                    '4/mm^2',
                    '>4/mm^2'})
        return value

    @classmethod
    def load(cls, value, acquisition, clinical, private):
        cls._checkWrite(clinical, cls.name, value)
        clinical[cls.name] = value


class MelUlcerFieldParser(FieldParser):
    name = 'mel_ulcer'
    allowedFields = {'mel_ulcer', 'ulcer'}

    @classmethod
    def transform(cls, value):
        if value is not None:
            value = value.strip()
            value = value.lower()
            if value in ['', 'unknown', 'not applicable']:
                value = None
            else:
                value = cls._coerceBool(value)
        return value

    @classmethod
    def load(cls, value, acquisition, clinical, private):
        cls._checkWrite(clinical, cls.name, value)
        clinical[cls.name] = value


class GeneralAnatomicSiteFieldParser(FieldParser):
    name = 'anatom_site_general'
    allowedFields = {'anatom_site_general'}

    @classmethod
    def transform(cls, value):
        if value is not None:
            value = value.strip()
            value = value.lower()
            if value in ['', 'unknown']:
                value = None
            else:
                cls._assertEnumerated(value, {
                    'head/neck',
                    'upper extremity',
                    'lower extremity',
                    'anterior torso',
                    'posterior torso',
                    'palms/soles',
                    'lateral torso',
                    'oral/genital',
                })
        return value

    @classmethod
    def load(cls, value, acquisition, clinical, private):
        cls._checkWrite(clinical, cls.name, value)
        clinical[cls.name] = value


class BlurryFieldParser(FieldParser):
    name = 'blurry'
    allowedFields = {'blurry'}

    @classmethod
    def transform(cls, value):
        if value is not None:
            value = value.strip()
            value = value.lower()
            if value in ['', 'unknown']:
                value = None
            else:
                value = cls._coerceBool(value)
        return value

    @classmethod
    def load(cls, value, acquisition, clinical, private):
        cls._checkWrite(acquisition, cls.name, value)
        acquisition[cls.name] = value


class ColorTintFieldParser(FieldParser):
    name = 'color_tint'
    allowedFields = {'colot_tint'}

    @classmethod
    def transform(cls, value):
        if value is not None:
            value = value.strip()
            value = value.lower()
            if value in ['', 'unknown']:
                value = None
            else:
                cls._assertEnumerated(value, {
                    'blue',
                    'pink',
                    'none',
                })
        return value

    @classmethod
    def load(cls, value, acquisition, clinical, private):
        cls._checkWrite(acquisition, cls.name, value)
        acquisition[cls.name] = value


class HairyFieldParser(FieldParser):
    name = 'hairy'
    allowedFields = {'hairy'}

    @classmethod
    def transform(cls, value):
        if value is not None:
            value = value.strip()
            value = value.lower()
            if value in ['', 'unknown']:
                value = None
            else:
                value = cls._coerceBool(value)
        return value

    @classmethod
    def load(cls, value, acquisition, clinical, private):
        cls._checkWrite(acquisition, cls.name, value)
        acquisition[cls.name] = value


class MarkerPenFieldParser(FieldParser):
    name = 'marker_pen'
    allowedFields = {'marker_pen'}

    @classmethod
    def transform(cls, value):
        if value is not None:
            value = value.strip()
            value = value.lower()
            if value in ['', 'unknown']:
                value = None
            else:
                value = cls._coerceBool(value)
        return value

    @classmethod
    def load(cls, value, acquisition, clinical, private):
        cls._checkWrite(acquisition, cls.name, value)
        acquisition[cls.name] = value


class PatientIdFieldParser(FieldParser):
    name = 'patient_id'
    allowedFields = {'patient_id'}

    @classmethod
    def transform(cls, value):
        if value is not None:
            value = value.strip()
            value = value.upper()
            if value in ['', 'UNKNOWN']:
                value = None
            elif not re.match('^IP_[0-9]{7}$', value):
                raise BadFieldTypeException(
                    name=cls.name, fieldType='of the form IP_1234567', value=value)
        return value

    @classmethod
    def load(cls, value, acquisition, clinical, private):
        cls._checkWrite(clinical, cls.name, value)
        clinical[cls.name] = value


class LesionIdFieldParser(FieldParser):
    name = 'lesion_id'
    allowedFields = {'lesion_id'}

    @classmethod
    def transform(cls, value):
        if value is not None:
            value = value.strip()
            value = value.upper()
            if value in ['', 'UNKNOWN']:
                value = None
            elif not re.match('^IL_[0-9]{7}$', value):
                raise BadFieldTypeException(
                    name=cls.name, fieldType='of the form IL_1234567', value=value)
        return value

    @classmethod
    def load(cls, value, acquisition, clinical, private):
        cls._checkWrite(clinical, cls.name, value)
        clinical[cls.name] = value


class AcquisitionDayFieldParser(FieldParser):
    name = 'acquisition_day'
    allowedFields = {'acquisition_day'}

    @classmethod
    def transform(cls, value):
        if value is not None:
            value = value.strip()
            value = value.lower()
            if value in ['', 'unknown']:
                value = None
            else:
                value = cls._coerceInt(value)
        return value

    @classmethod
    def load(cls, value, acquisition, clinical, private):
        cls._checkWrite(acquisition, cls.name, value)
        acquisition[cls.name] = value


def _populateMetadata(acquisition, clinical):
    """
    Populate empty metadata fields that can be determined based on other fields.

    In some cases, populates inconsistent fields and emits a warning.
    Returns a list of warnings.
    """
    warnings = []

    dermoscopicType = acquisition.get('dermoscopic_type')
    imageType = acquisition.get('image_type')

    diagnosis = clinical.get('diagnosis')
    benignMalignant = clinical.get('benign_malignant')
    diagnosisConfirmType = clinical.get('diagnosis_confirm_type')
    melanocytic = clinical.get('melanocytic')

    if diagnosis == 'melanoma':
        if benignMalignant is None:
            clinical['benign_malignant'] = 'malignant'
    elif diagnosis == 'nevus':
        if benignMalignant is None and diagnosisConfirmType not in [None, 'histopathology']:
            clinical['benign_malignant'] = 'benign'

    # Set melanocytic field based on diagnosis
    if diagnosis in MelanocyticFieldParser.melanocyticDiagnoses:
        if melanocytic is None:
            clinical['melanocytic'] = True
        elif not melanocytic:
            clinical['melanocytic'] = True
            warnings.append('corrected inconsistent value for field %r based on field %r '
                            '(new value: %r, %r: %r)' %
                            (MelanocyticFieldParser.name, DiagnosisFieldParser.name,
                             True, DiagnosisFieldParser.name, diagnosis))
    elif diagnosis is not None and diagnosis != 'other':
        if melanocytic is None:
            clinical['melanocytic'] = False
        elif melanocytic:
            clinical['melanocytic'] = False
            warnings.append('corrected inconsistent value for field %r based on field %r '
                            '(new value: %r, %r: %r)' %
                            (MelanocyticFieldParser.name, DiagnosisFieldParser.name,
                             False, DiagnosisFieldParser.name, diagnosis))

    if dermoscopicType is not None and imageType is None:
        acquisition['image_type'] = 'dermoscopic'

    return warnings


def _checkMetadataErrors(acquisition, clinical):
    """
    Check metadata for fatal errors with respect to consistency between fields.

    Raises an InconsistentValuesException is raised if a value violates a rule.
    """
    dermoscopicType = acquisition.get('dermoscopic_type')
    imageType = acquisition.get('image_type')

    diagnosis = clinical.get('diagnosis')
    benignMalignant = clinical.get('benign_malignant')
    diagnosisConfirmType = clinical.get('diagnosis_confirm_type')
    melThickMm = clinical.get('mel_thick_mm')
    melClass = clinical.get('mel_class')
    melType = clinical.get('mel_type')
    melMitoticIndex = clinical.get('mel_mitotic_index')
    melUlcer = clinical.get('mel_ulcer')
    nevusType = clinical.get('nevus_type')

    if diagnosis == 'melanoma':
        if benignMalignant != 'malignant':
            raise InconsistentValuesException(
                names=[DiagnosisFieldParser.name, BenignMalignantFieldParser.name],
                values=[diagnosis, benignMalignant])
    elif diagnosis == 'nevus':
        if benignMalignant not in [
            'benign',
            'indeterminate/benign',
            'indeterminate',
        ]:
            raise InconsistentValuesException(
                names=[DiagnosisFieldParser.name, BenignMalignantFieldParser.name],
                values=[diagnosis, benignMalignant])

    # Verify melanoma-related fields with respect to diagnosis
    for value, parser in [
        (melThickMm, MelThickMmFieldParser),
        (melClass, MelClassFieldParser),
        (melType, MelTypeFieldParser),
        (melMitoticIndex, MelMitoticIndexFieldParser),
        (melUlcer, MelUlcerFieldParser)
    ]:
        if value is not None and diagnosis != 'melanoma':
            raise InconsistentValuesException(
                names=[parser.name, DiagnosisFieldParser.name],
                values=[value, diagnosis])

    if benignMalignant in [
        'indeterminate/benign',
        'indeterminate/malignant',
        'indeterminate',
        'malignant',
    ] and diagnosisConfirmType != 'histopathology':
        raise InconsistentValuesException(
            names=[BenignMalignantFieldParser.name, DiagnosisConfirmTypeFieldParser.name],
            values=[benignMalignant, diagnosisConfirmType])

    # Verify nevus type field with respect to diagnosis
    if nevusType is not None and diagnosis not in ['nevus', 'nevus spilus']:
        raise InconsistentValuesException(
            names=[DiagnosisFieldParser.name, NevusTypeFieldParser.name],
            values=[diagnosis, nevusType])

    if imageType != 'dermoscopic' and dermoscopicType is not None:
        raise InconsistentValuesException(
            names=[ImageTypeFieldParser.name, DermoscopicTypeFieldParser.name],
            values=[imageType, dermoscopicType])


def _checkMetadataWarnings(clinical):
    """
    Check metadata for non-fatal warnings with respect to consistency between fields.

    Returns a list of warnings.
    """
    warnings = []

    diagnosis = clinical.get('diagnosis')
    benignMalignant = clinical.get('benign_malignant')

    if diagnosis in [
        'basal cell carcinoma',
        'squamous cell carcinoma',
    ] and benignMalignant in [
        'benign',
        'indeterminate/benign',
    ]:
        warnings.append('%r is typically not %r' % (diagnosis, benignMalignant))

    return warnings


def _extractExifMetadata(data: Dict, unstructuredExif: Dict):
    """
    Add EXIF-related metadata to its own unstructured field.

    :param data: The image metadata.
    :param unstructuredExif: The dictionary of unstructured EXIF metadata.
    """
    for key in list(data.keys()):
        if key.lower().startswith('exif_'):
            unstructuredExif[key] = data.pop(key)


def addImageMetadata(image: Dict, data: Dict) -> Tuple[List[str], List[str]]:
    """
    Add acquisition and clinical metadata to an image.

    Data is expected to be a dict, such as a row from csv.DictReader. Values for recognized fields
    are parsed and added to the image's clinical metadata field and private metadata
    field. Unrecognized fields are added to the image's unstructured metadata field.

    Returns a tuple of:
    - List of descriptive errors with the metadata. An empty list indicates that
      there are no errors.
    - List of warnings about the metadata. To avoid erroneous entries, this is
      populated only when there are no errors.

    :param image: The image.
    :param data: The image metadata.
    :return: Tuple of (errors, warnings)
    """
    # Operate on copy of image metadata
    data = copy.deepcopy(data)

    errors: List[str] = []
    warnings: List[str] = []

    for parser in [
        AgeFieldParser,
        SexFieldParser,
        FamilyHxMmFieldParser,
        PersonalHxMmFieldParser,
        ClinicalSizeFieldParser,
        MelanocyticFieldParser,
        DiagnosisConfirmTypeFieldParser,
        BenignMalignantFieldParser,
        DiagnosisFieldParser,
        NevusTypeFieldParser,
        ImageTypeFieldParser,
        DermoscopicTypeFieldParser,
        MelThickMmFieldParser,
        MelClassFieldParser,
        MelTypeFieldParser,
        MelMitoticIndexFieldParser,
        MelUlcerFieldParser,
        GeneralAnatomicSiteFieldParser,
        BlurryFieldParser,
        ColorTintFieldParser,
        HairyFieldParser,
        MarkerPenFieldParser,
        PatientIdFieldParser,
        LesionIdFieldParser,
        AcquisitionDayFieldParser,
    ]:
        acquisition = image['meta']['acquisition']
        clinical = image['meta']['clinical']
        private = image['privateMeta']

        try:
            parser.run(data, acquisition, clinical, private)
        except MetadataValueExistsException as e:
            errors.append(
                'value already exists for field %r (old: %r, new: %r)' %
                (e.name, e.oldValue, e.newValue))
        except MultipleFieldException as e:
            errors.append(
                'only one of field %r may be present, found: %r' %
                (e.name, e.fields))
        except BadFieldTypeException as e:
            errors.append(
                'value is wrong type for field %r (expected %r, value: %r)' %
                (e.name, e.fieldType, e.value))

    # TODO: handle contingently required fields

    # Populate empty metadata fields
    warnings.extend(_populateMetadata(acquisition, clinical))

    # Check metadata for errors
    try:
        _checkMetadataErrors(acquisition, clinical)
    except InconsistentValuesException as e:
        errors.append('values %r for fields %r are inconsistent' % (e.values, e.names))

    # Check metadata for warnings
    warnings.extend(_checkMetadataWarnings(clinical))

    # Add EXIF-related metadata to its own unstructured field
    _extractExifMetadata(data, image['meta']['unstructuredExif'])

    # Add remaining data as unstructured metadata
    image['meta']['unstructured'].update(data)

    # Report warnings for unrecognized fields when there are no errors
    if not errors:
        warnings.extend([
            f'unrecognized field {field!r} will be added to unstructured metadata'
            for field in data])

    return errors, warnings
