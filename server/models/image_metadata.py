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

import six


class FieldParser(object):
    name = ''
    allowedFields = {}
    private = False

    @classmethod
    def run(cls, unstructured, clinical, private):
        rawValue = cls.extract(unstructured)
        cleanValue = cls.transform(rawValue)
        cls.load(cleanValue, clinical, private)

    @classmethod
    def extract(cls, unstructured):
        availableFields = set(key.lower() for key in six.viewkeys(unstructured))

        foundFields = availableFields & cls.allowedFields
        if not foundFields:
            return None
        elif len(foundFields) == 1:
            # TODO: return without popping
            return unstructured.pop(foundFields.pop())
        else:
            raise Exception(
                'only one of %s may be present' % sorted(foundFields))

    @classmethod
    def transform(cls, value):
        raise NotImplementedError()

    @classmethod
    def load(cls, value, clinical, private):
        if value is not None:
            outputDict = private if cls.private else clinical
            # TODO: refuse to overwrite if the value is different
            outputDict[cls.name] = value

    @classmethod
    def _coerceInt(cls, value):
        try:
            value = int(float(value))
        except ValueError:
            raise Exception('value of "%s" must be an integer' % value)
        return value

    @classmethod
    def _coerceFloat(cls, value):
        try:
            value = float(value)
        except ValueError:
            raise Exception('value of "%s" must be a float' % value)
        return value

    @classmethod
    def _coerceBool(cls, value):
        if value in ['true', 'yes']:
            return True
        elif value in ['false', 'no']:
            return False
        else:
            raise Exception('value of "%s" must be a boolean' % value)

    @classmethod
    def _assertEnumerated(cls, value, allowed):
        if value not in allowed:
            raise Exception(
                'value of "%s" must be one of: %s' % (value, sorted(allowed)))


class AgeFieldParser(FieldParser):
    name = 'age'
    allowedFields = {'age'}
    private = True

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
    def load(cls, value, clinical, private):
        if value is not None:
            # TODO: refuse to overwrite if the value is different
            private['age'] = value
            clinical['age_approx'] = \
                int(round(value / 5.0) * 5) \
                if value is not None \
                else None


class SexFieldParser(FieldParser):
    name = 'sex'
    allowedFields = {'sex', 'gender'}
    private = False

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


class FamilyHxMmFieldParser(HxMmFieldParser):
    name = 'family_hx_mm'
    allowedFields = {'family_hx_mm', 'FamHxMM'}
    private = False


class PersonalHxMmFieldParser(HxMmFieldParser):
    name = 'personal_hx_mm'
    allowedFields = {'personal_hx_mm'}
    private = False


class ClinicalSizeFieldParser(FieldParser):
    name = 'clin_size_long_diam_mm'
    allowedFields = {'clin_size_long_diam_mm'}
    private = False

    @classmethod
    def transform(cls, value):
        if value is not None:
            value = value.strip()
            value = value.lower()
            if value in ['', 'unknown']:
                value = None
            else:
                value = cls._coerceFloat(value)
        return value


class MelanocyticFieldParser(FieldParser):
    name = 'melanocytic'
    allowedFields = {'melanocytic'}
    private = False

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


class DiagnosisConfirmTypeFieldParser(FieldParser):
    name = 'diagnosis_confirm_type'
    allowedFields = {'diagnosis_confirm_type'}
    private = False

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
                    'single image expert consensus'})
        return value


class BenignMalignantFieldParser(FieldParser):
    name = 'benign_malignant'
    allowedFields = {'benign_malignant', 'ben_mal'}
    private = False

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

    #     if value is not None:


# if 'diagnosis_confirm_type' not in clinical:
#             # TODO: remove this, it's always going to be there
#             raise Exception('"diagnosis_confirm_type" must also be set')

#         if value in {'malignant', 'indeterminate/malignant'}:
#             if clinical['diagnosis_confirm_type'] != 'histopathology':
#                 raise Exception('if this value is "malignant", "diagnosis_confirm_type" must be "histopathology"')


class DiagnosisFieldParser(FieldParser):
    name = 'diagnosis'
    allowedFields = {'diagnosis', 'path_diagnosis'}
    private = False

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
                elif value == u'caf\xe9-au-lait macule':
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
                    'other'})
        return value


class NevusTypeFieldParser(FieldParser):
    name = 'nevus_type'
    allowedFields = {'nevus_type'}
    private = False

    @classmethod
    def transform(cls, value):
        if value is not None:
            value = value.strip()
            value = value.lower()
            if value in ['', 'unknown']:
                value = None
            elif value == 'not applicable':
                value = None
            else:
                # TODO: finish this
                cls._assertEnumerated(value, {
                    'blue',
                    'combined',
                    'nevus NOS',
                    'deep penetrating',
                    'halo',
                    'other',
                    'persistent/recurrent',
                    'pigmented spindle cell of reed',
                    'plexiform spindle cell',
                    'special site',
                    'spitz',
                    #             'not applicable'
                    'unknown'})
        return value

    #     if 'diagnosis' in clinical:


# allowed_diagnoses = {'nevus', 'nevus spilus', 'epidermal nevus'}
#         if clinical['path_diagnosis'] not in allowed_diagnoses:
#             raise Exception('if this value is set, "path_diagnosis" must be one of %s' % sorted(allowed_diagnoses))


def addImageClinicalMetadata(image):
    # TODO: how are blank cells parsed by csvreader?
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
        #         NevusTypeFieldParser,
    ]:
        parser.run(
            unstructured=image['meta']['unstructured'],
            clinical=image['meta']['clinical'],
            private=image['privateMeta']
        )
