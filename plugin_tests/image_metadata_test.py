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

import os
import sys

from tests import base

MetadataFieldException = None
MetadataFieldNotFoundException = None
MetadataValueExistsException = None
MultipleFieldException = None
BadFieldTypeException = None

AgeFieldParser = None
SexFieldParser = None
FamilyHxMmFieldParser = None
PersonalHxMmFieldParser = None
ClinicalSizeFieldParser = None
MelanocyticFieldParser = None
DiagnosisConfirmTypeFieldParser = None
BenignMalignantFieldParser = None
DiagnosisFieldParser = None
ImageTypeFieldParser = None
DermoscopicTypeFieldParser = None
MelThickMmFieldParser = None
MelClassFieldParser = None

addImageMetadata = None


def setUpModule():
    isicModelsModulePath = os.path.abspath(os.path.join(
        os.path.dirname(__file__), '..', 'server', 'models'))
    if isicModelsModulePath not in sys.path:
        sys.path.append(isicModelsModulePath)

    global \
        MetadataFieldException, \
        MetadataFieldNotFoundException, \
        MetadataValueExistsException, \
        MultipleFieldException, \
        BadFieldTypeException, \
        AgeFieldParser, \
        SexFieldParser, \
        FamilyHxMmFieldParser, \
        PersonalHxMmFieldParser, \
        ClinicalSizeFieldParser, \
        MelanocyticFieldParser, \
        DiagnosisConfirmTypeFieldParser, \
        BenignMalignantFieldParser, \
        DiagnosisFieldParser, \
        ImageTypeFieldParser, \
        DermoscopicTypeFieldParser, \
        MelThickMmFieldParser, \
        MelClassFieldParser, \
        addImageMetadata
    from dataset_helpers.image_metadata import \
        MetadataFieldException, \
        MetadataFieldNotFoundException, \
        MetadataValueExistsException, \
        MultipleFieldException, \
        BadFieldTypeException, \
        AgeFieldParser, \
        SexFieldParser, \
        FamilyHxMmFieldParser, \
        PersonalHxMmFieldParser, \
        ClinicalSizeFieldParser, \
        MelanocyticFieldParser, \
        DiagnosisConfirmTypeFieldParser, \
        BenignMalignantFieldParser, \
        DiagnosisFieldParser, \
        ImageTypeFieldParser, \
        DermoscopicTypeFieldParser, \
        MelThickMmFieldParser, \
        MelClassFieldParser, \
        addImageMetadata


class ImageMetadataTestCase(base.TestCase):
    """Test image metadata parsers and error reporting."""
    def setUp(self):
        # A Girder instance is not required for this test case

        # Values that parsers should record as None
        self.unknownValues = [None, '', 'unknown', 'UNKNOWN']

    def _createImage(self):
        """Create an empty mock image object."""
        image = {
            'meta': {
                'acquisition': {},
                'clinical': {},
                'unstructured': {}
            },
            'privateMeta': {}
        }
        return image

    def _runParser(self, image, data, parser):
        acquisition = image['meta']['acquisition']
        clinical = image['meta']['clinical']
        private = image['privateMeta']
        parser.run(data, acquisition, clinical, private)

    def assertRunParser(self, image, data, parser):
        """Assert that the parser runs without raising a MetadataFieldException."""
        try:
            self._runParser(image, data, parser)
        except MetadataFieldException:
            self.fail('Unexpected MetadataFieldException')

    def assertRunParserRaises(self, image, data, parser, exception):
        """Assert that running the parser raises the specified exception type."""
        with self.assertRaises(exception):
            self._runParser(image, data, parser)

    def _testFieldNotFound(self, parser):
        """
        Convenience method to test that a parser makes no changes if none of its
        allowed fields are given in the metadata.
        """
        data = {'other': 'value'}
        image = self._createImage()
        self.assertRunParser(image, data, parser)
        self.assertDictEqual({'other': 'value'}, data)
        self.assertDictEqual({}, image['meta']['acquisition'])
        self.assertDictEqual({}, image['meta']['clinical'])
        self.assertDictEqual({}, image['meta']['unstructured'])
        self.assertDictEqual({}, image['privateMeta'])

    def testAgeFieldParser(self):
        parser = AgeFieldParser

        # Multiple of 5
        data = {'age': '25'}
        image = self._createImage()
        self.assertRunParser(image, data, parser)
        self.assertDictEqual({}, data)
        self.assertDictEqual({}, image['meta']['unstructured'])
        self.assertDictEqual({'age_approx': 25}, image['meta']['clinical'])
        self.assertDictEqual({'age': 25}, image['privateMeta'])

        # Not a multiple of 5
        data = {'age': '38'}
        image = self._createImage()
        self.assertRunParser(image, data, parser)
        self.assertDictEqual({}, data)
        self.assertDictEqual({}, image['meta']['unstructured'])
        self.assertDictEqual({'age_approx': 40}, image['meta']['clinical'])
        self.assertDictEqual({'age': 38}, image['privateMeta'])

        # Special maximum value
        data = {'age': '85+'}
        image = self._createImage()
        self.assertRunParser(image, data, parser)
        self.assertDictEqual({}, data)
        self.assertDictEqual({}, image['meta']['unstructured'])
        self.assertDictEqual({'age_approx': 85}, image['meta']['clinical'])
        self.assertDictEqual({'age': 85}, image['privateMeta'])

        # Greater than maximum
        data = {'age': '86'}
        image = self._createImage()
        self.assertRunParser(image, data, parser)
        self.assertDictEqual({}, data)
        self.assertDictEqual({}, image['meta']['unstructured'])
        self.assertDictEqual({'age_approx': 85}, image['meta']['clinical'])
        self.assertDictEqual({'age': 85}, image['privateMeta'])

        # Mixed case field name
        data = {'Age': '25'}
        image = self._createImage()
        self.assertRunParser(image, data, parser)
        self.assertDictEqual({}, data)
        self.assertDictEqual({}, image['meta']['unstructured'])
        self.assertDictEqual({'age_approx': 25}, image['meta']['clinical'])
        self.assertDictEqual({'age': 25}, image['privateMeta'])

        # Unknown values
        for value in self.unknownValues:
            data = {'age': value}
            image = self._createImage()
            self.assertRunParser(image, data, parser)
            self.assertDictEqual({}, data)
            self.assertDictEqual({}, image['meta']['unstructured'])
            self.assertDictEqual({'age_approx': None}, image['meta']['clinical'])
            self.assertDictEqual({'age': None}, image['privateMeta'])

        # Update null value with new value
        data = {'age': '25'}
        image = self._createImage()
        image['meta']['clinical'] = {'age_approx': None}
        image['privateMeta']['age'] = None
        self.assertRunParser(image, data, parser)
        self.assertDictEqual({}, data)
        self.assertDictEqual({}, image['meta']['unstructured'])
        self.assertDictEqual({'age_approx': 25}, image['meta']['clinical'])
        self.assertDictEqual({'age': 25}, image['privateMeta'])

        # Update existing value with same value
        data = {'age': '25'}
        image = self._createImage()
        image['meta']['clinical']['age_approx'] = 25
        image['privateMeta']['age'] = 25
        self.assertRunParser(image, data, parser)
        self.assertDictEqual({}, data)
        self.assertDictEqual({}, image['meta']['unstructured'])
        self.assertDictEqual({'age_approx': 25}, image['meta']['clinical'])
        self.assertDictEqual({'age': 25}, image['privateMeta'])

        # Update existing value with null value
        data = {'age': None}
        image = self._createImage()
        image['meta']['clinical']['age_approx'] = 25
        image['privateMeta']['age'] = 25
        self.assertRunParserRaises(image, data, parser, MetadataValueExistsException)

        # Update existing value with new value
        data = {'age': '50'}
        image = self._createImage()
        image['meta']['clinical']['age_approx'] = 25
        image['privateMeta']['age'] = 25
        self.assertRunParserRaises(image, data, parser, MetadataValueExistsException)

        # Field not found
        self._testFieldNotFound(parser)

        # Bad field type
        data = {'age': 'true'}
        image = self._createImage()
        self.assertRunParserRaises(image, data, parser, BadFieldTypeException)

    def testSexFieldParser(self):
        parser = SexFieldParser

        # Abbreviation, lowercase
        data = {'sex': 'f'}
        image = self._createImage()
        self.assertRunParser(image, data, parser)
        self.assertDictEqual({}, data)
        self.assertDictEqual({}, image['meta']['unstructured'])
        self.assertDictEqual({'sex': 'female'}, image['meta']['clinical'])
        self.assertDictEqual({}, image['privateMeta'])

        # Abbreviation, uppercase
        data = {'sex': 'M'}
        image = self._createImage()
        self.assertRunParser(image, data, parser)
        self.assertDictEqual({}, data)
        self.assertDictEqual({}, image['meta']['unstructured'])
        self.assertDictEqual({'sex': 'male'}, image['meta']['clinical'])
        self.assertDictEqual({}, image['privateMeta'])

        # Unabbreviated, mixed case
        data = {'sex': 'Female'}
        image = self._createImage()
        self.assertRunParser(image, data, parser)
        self.assertDictEqual({}, data)
        self.assertDictEqual({}, image['meta']['unstructured'])
        self.assertDictEqual({'sex': 'female'}, image['meta']['clinical'])
        self.assertDictEqual({}, image['privateMeta'])

        # Alternative field name
        data = {'gender': 'f'}
        image = self._createImage()
        self.assertRunParser(image, data, parser)
        self.assertDictEqual({}, data)
        self.assertDictEqual({}, image['meta']['unstructured'])
        self.assertDictEqual({'sex': 'female'}, image['meta']['clinical'])
        self.assertDictEqual({}, image['privateMeta'])

        # Mixed case field name
        data = {'Gender': 'f'}
        image = self._createImage()
        self.assertRunParser(image, data, parser)
        self.assertDictEqual({}, data)
        self.assertDictEqual({}, image['meta']['unstructured'])
        self.assertDictEqual({'sex': 'female'}, image['meta']['clinical'])
        self.assertDictEqual({}, image['privateMeta'])

        # Unknown values
        for value in self.unknownValues:
            data = {'sex': value}
            image = self._createImage()
            self.assertRunParser(image, data, parser)
            self.assertDictEqual({}, data)
            self.assertDictEqual({}, image['meta']['unstructured'])
            self.assertDictEqual({'sex': None}, image['meta']['clinical'])
            self.assertDictEqual({}, image['privateMeta'])

        # Duplicate field
        data = {'gender': 'f', 'sex': 'f'}
        image = self._createImage()
        self.assertRunParserRaises(image, data, parser, MultipleFieldException)

        # Update null value with new value
        data = {'gender': 'f'}
        image = self._createImage()
        image['meta']['clinical']['sex'] = None
        self.assertRunParser(image, data, parser)
        self.assertDictEqual({}, data)
        self.assertDictEqual({}, image['meta']['unstructured'])
        self.assertDictEqual({'sex': 'female'}, image['meta']['clinical'])
        self.assertDictEqual({}, image['privateMeta'])

        # Update existing value with same value
        data = {'gender': 'f'}
        image = self._createImage()
        image['meta']['clinical']['sex'] = 'female'
        self.assertRunParser(image, data, parser)
        self.assertDictEqual({}, data)
        self.assertDictEqual({}, image['meta']['unstructured'])
        self.assertDictEqual({'sex': 'female'}, image['meta']['clinical'])
        self.assertDictEqual({}, image['privateMeta'])

        # Update existing value with null value
        data = {'gender': None}
        image = self._createImage()
        image['meta']['clinical']['sex'] = 'female'
        self.assertRunParserRaises(image, data, parser, MetadataValueExistsException)

        # Update existing value with new value
        data = {'gender': 'm'}
        image = self._createImage()
        image['meta']['clinical']['sex'] = 'female'
        self.assertRunParserRaises(image, data, parser, MetadataValueExistsException)

        # Field not found
        self._testFieldNotFound(parser)

        # Bad field type
        data = {'sex': 'true'}
        image = self._createImage()
        self.assertRunParserRaises(image, data, parser, BadFieldTypeException)

    def testFamilyHxMmFieldParser(self):
        parser = FamilyHxMmFieldParser

        # Standard field name
        data = {'family_hx_mm': 'true'}
        image = self._createImage()
        self.assertRunParser(image, data, parser)
        self.assertDictEqual({}, data)
        self.assertDictEqual({}, image['meta']['unstructured'])
        self.assertDictEqual({'family_hx_mm': True}, image['meta']['clinical'])
        self.assertDictEqual({}, image['privateMeta'])

        # Alternative field name
        data = {'FamHxMM': 'true'}
        image = self._createImage()
        self.assertRunParser(image, data, parser)
        self.assertDictEqual({}, data)
        self.assertDictEqual({}, image['meta']['unstructured'])
        self.assertDictEqual({'family_hx_mm': True}, image['meta']['clinical'])
        self.assertDictEqual({}, image['privateMeta'])

        # Unknown values
        for value in self.unknownValues:
            data = {'family_hx_mm': value}
            image = self._createImage()
            self.assertRunParser(image, data, parser)
            self.assertDictEqual({}, data)
            self.assertDictEqual({}, image['meta']['unstructured'])
            self.assertDictEqual({'family_hx_mm': None}, image['meta']['clinical'])
            self.assertDictEqual({}, image['privateMeta'])

        # Duplicate field
        data = {'family_hx_mm': 'false', 'FamHxMM': 'false'}
        image = self._createImage()
        self.assertRunParserRaises(image, data, parser, MultipleFieldException)

        # Update null value with new value
        data = {'family_hx_mm': 'false'}
        image = self._createImage()
        image['meta']['clinical']['family_hx_mm'] = None
        self.assertRunParser(image, data, parser)
        self.assertDictEqual({}, data)
        self.assertDictEqual({}, image['meta']['unstructured'])
        self.assertDictEqual({'family_hx_mm': False}, image['meta']['clinical'])
        self.assertDictEqual({}, image['privateMeta'])

        # Update existing value with same value
        data = {'family_hx_mm': 'false'}
        image = self._createImage()
        image['meta']['clinical']['family_hx_mm'] = False
        self.assertRunParser(image, data, parser)
        self.assertDictEqual({}, data)
        self.assertDictEqual({}, image['meta']['unstructured'])
        self.assertDictEqual({'family_hx_mm': False}, image['meta']['clinical'])
        self.assertDictEqual({}, image['privateMeta'])

        # Update existing value with null value
        data = {'family_hx_mm': None}
        image = self._createImage()
        image['meta']['clinical']['family_hx_mm'] = False
        self.assertRunParserRaises(image, data, parser, MetadataValueExistsException)

        # Update existing value with new value
        data = {'family_hx_mm': 'true'}
        image = self._createImage()
        image['meta']['clinical']['family_hx_mm'] = False
        self.assertRunParserRaises(image, data, parser, MetadataValueExistsException)

        # Field not found
        self._testFieldNotFound(parser)

        # Bad field type
        data = {'family_hx_mm': '1'}
        image = self._createImage()
        self.assertRunParserRaises(image, data, parser, BadFieldTypeException)

    def testPersonalHxMmFieldParser(self):
        parser = PersonalHxMmFieldParser

        # Normal
        data = {'personal_hx_mm': 'true'}
        image = self._createImage()
        self.assertRunParser(image, data, parser)
        self.assertDictEqual({}, data)
        self.assertDictEqual({}, image['meta']['unstructured'])
        self.assertDictEqual({'personal_hx_mm': True}, image['meta']['clinical'])
        self.assertDictEqual({}, image['privateMeta'])

        # Normal, alternative value representation
        data = {'personal_hx_mm': 'no'}
        image = self._createImage()
        self.assertRunParser(image, data, parser)
        self.assertDictEqual({}, data)
        self.assertDictEqual({}, image['meta']['unstructured'])
        self.assertDictEqual({'personal_hx_mm': False}, image['meta']['clinical'])
        self.assertDictEqual({}, image['privateMeta'])

        # Unknown values
        for value in self.unknownValues:
            data = {'personal_hx_mm': value}
            image = self._createImage()
            self.assertRunParser(image, data, parser)
            self.assertDictEqual({}, data)
            self.assertDictEqual({}, image['meta']['unstructured'])
            self.assertDictEqual({'personal_hx_mm': None}, image['meta']['clinical'])
            self.assertDictEqual({}, image['privateMeta'])

        # Update null value with new value
        data = {'personal_hx_mm': 'false'}
        image = self._createImage()
        image['meta']['clinical']['personal_hx_mm'] = None
        self.assertRunParser(image, data, parser)
        self.assertDictEqual({}, data)
        self.assertDictEqual({}, image['meta']['unstructured'])
        self.assertDictEqual({'personal_hx_mm': False}, image['meta']['clinical'])
        self.assertDictEqual({}, image['privateMeta'])

        # Update existing value with same value
        data = {'personal_hx_mm': 'false'}
        image = self._createImage()
        image['meta']['clinical']['personal_hx_mm'] = False
        self.assertRunParser(image, data, parser)
        self.assertDictEqual({}, data)
        self.assertDictEqual({}, image['meta']['unstructured'])
        self.assertDictEqual({'personal_hx_mm': False}, image['meta']['clinical'])
        self.assertDictEqual({}, image['privateMeta'])

        # Update existing value with null value
        data = {'personal_hx_mm': None}
        image = self._createImage()
        image['meta']['clinical']['personal_hx_mm'] = False
        self.assertRunParserRaises(image, data, parser, MetadataValueExistsException)

        # Update existing value with new value
        data = {'personal_hx_mm': 'true'}
        image = self._createImage()
        image['meta']['clinical']['personal_hx_mm'] = False
        self.assertRunParserRaises(image, data, parser, MetadataValueExistsException)

        # Field not found
        self._testFieldNotFound(parser)

        # Bad field type
        data = {'personal_hx_mm': '1'}
        image = self._createImage()
        self.assertRunParserRaises(image, data, parser, BadFieldTypeException)

    def testClinicalSizeFieldParser(self):
        parser = ClinicalSizeFieldParser

        # Normal, um
        data = {'clin_size_long_diam_mm': '1500.0 um'}
        image = self._createImage()
        self.assertRunParser(image, data, parser)
        self.assertDictEqual({}, data)
        self.assertDictEqual({}, image['meta']['unstructured'])
        self.assertDictEqual({'clin_size_long_diam_mm': 1.5}, image['meta']['clinical'])
        self.assertDictEqual({}, image['privateMeta'])

        # Normal, mm
        data = {'clin_size_long_diam_mm': '1.5 mm'}
        image = self._createImage()
        self.assertRunParser(image, data, parser)
        self.assertDictEqual({}, data)
        self.assertDictEqual({}, image['meta']['unstructured'])
        self.assertDictEqual({'clin_size_long_diam_mm': 1.5}, image['meta']['clinical'])
        self.assertDictEqual({}, image['privateMeta'])

        # Normal, cm
        data = {'clin_size_long_diam_mm': '1.5 cm'}
        image = self._createImage()
        self.assertRunParser(image, data, parser)
        self.assertDictEqual({}, data)
        self.assertDictEqual({}, image['meta']['unstructured'])
        self.assertDictEqual({'clin_size_long_diam_mm': 15.0}, image['meta']['clinical'])
        self.assertDictEqual({}, image['privateMeta'])

        # Unknown values
        for value in self.unknownValues:
            data = {'clin_size_long_diam_mm': value}
            image = self._createImage()
            self.assertRunParser(image, data, parser)
            self.assertDictEqual({}, data)
            self.assertDictEqual({}, image['meta']['unstructured'])
            self.assertDictEqual({'clin_size_long_diam_mm': None}, image['meta']['clinical'])
            self.assertDictEqual({}, image['privateMeta'])

        # Update null value with new value
        data = {'clin_size_long_diam_mm': '1.5 mm'}
        image = self._createImage()
        image['meta']['clinical']['clin_size_long_diam_mm'] = None
        self.assertRunParser(image, data, parser)
        self.assertDictEqual({}, data)
        self.assertDictEqual({}, image['meta']['unstructured'])
        self.assertDictEqual({'clin_size_long_diam_mm': 1.5}, image['meta']['clinical'])
        self.assertDictEqual({}, image['privateMeta'])

        # Update existing value with same value
        data = {'clin_size_long_diam_mm': '1.5 mm'}
        image = self._createImage()
        image['meta']['clinical']['clin_size_long_diam_mm'] = 1.5
        self.assertRunParser(image, data, parser)
        self.assertDictEqual({}, data)
        self.assertDictEqual({}, image['meta']['unstructured'])
        self.assertDictEqual({'clin_size_long_diam_mm': 1.5}, image['meta']['clinical'])
        self.assertDictEqual({}, image['privateMeta'])

        # Update existing value with null value
        data = {'clin_size_long_diam_mm': None}
        image = self._createImage()
        image['meta']['clinical']['clin_size_long_diam_mm'] = 1.5
        self.assertRunParserRaises(image, data, parser, MetadataValueExistsException)

        # Update existing value with new value
        data = {'clin_size_long_diam_mm': '1.5 mm'}
        image = self._createImage()
        image['meta']['clinical']['clin_size_long_diam_mm'] = 2.0
        self.assertRunParserRaises(image, data, parser, MetadataValueExistsException)

        # Field not found
        self._testFieldNotFound(parser)

        # Bad field type
        data = {'clin_size_long_diam_mm': 'true'}
        image = self._createImage()
        self.assertRunParserRaises(image, data, parser, BadFieldTypeException)

        data = {'clin_size_long_diam_mm': '0.001 m'}
        image = self._createImage()
        self.assertRunParserRaises(image, data, parser, BadFieldTypeException)

        data = {'clin_size_long_diam_mm': 'inf'}
        image = self._createImage()
        self.assertRunParserRaises(image, data, parser, BadFieldTypeException)

        data = {'clin_size_long_diam_mm': 'inf mm'}
        image = self._createImage()
        self.assertRunParserRaises(image, data, parser, BadFieldTypeException)

    def testMelanocyticFieldParser(self):
        parser = MelanocyticFieldParser

        # Normal
        data = {'melanocytic': 'false'}
        image = self._createImage()
        self.assertRunParser(image, data, parser)
        self.assertDictEqual({}, data)
        self.assertDictEqual({}, image['meta']['unstructured'])
        self.assertDictEqual({'melanocytic': False}, image['meta']['clinical'])
        self.assertDictEqual({}, image['privateMeta'])

        # Unknown values
        for value in self.unknownValues:
            data = {'melanocytic': value}
            image = self._createImage()
            self.assertRunParser(image, data, parser)
            self.assertDictEqual({}, data)
            self.assertDictEqual({}, image['meta']['unstructured'])
            self.assertDictEqual({'melanocytic': None}, image['meta']['clinical'])
            self.assertDictEqual({}, image['privateMeta'])

        # Update null value with new value
        data = {'melanocytic': 'true'}
        image = self._createImage()
        image['meta']['clinical']['melanocytic'] = None
        self.assertRunParser(image, data, parser)
        self.assertDictEqual({}, data)
        self.assertDictEqual({}, image['meta']['unstructured'])
        self.assertDictEqual({'melanocytic': True}, image['meta']['clinical'])
        self.assertDictEqual({}, image['privateMeta'])

        # Update existing value with same value
        data = {'melanocytic': 'true'}
        image = self._createImage()
        image['meta']['clinical']['melanocytic'] = True
        self.assertRunParser(image, data, parser)
        self.assertDictEqual({}, data)
        self.assertDictEqual({}, image['meta']['unstructured'])
        self.assertDictEqual({'melanocytic': True}, image['meta']['clinical'])
        self.assertDictEqual({}, image['privateMeta'])

        # Update existing value with null value
        data = {'melanocytic': None}
        image = self._createImage()
        image['meta']['clinical']['melanocytic'] = True
        self.assertRunParserRaises(image, data, parser, MetadataValueExistsException)

        # Update existing value with new value
        data = {'melanocytic': 'true'}
        image = self._createImage()
        image['meta']['clinical']['melanocytic'] = False
        self.assertRunParserRaises(image, data, parser, MetadataValueExistsException)

        # Field not found
        self._testFieldNotFound(parser)

        # Bad field type
        data = {'melanocytic': '1'}
        image = self._createImage()
        self.assertRunParserRaises(image, data, parser, BadFieldTypeException)

    def testDiagnosisConfirmTypeFieldParser(self):
        parser = DiagnosisConfirmTypeFieldParser

        # Valid values with varying case
        for value in [
            'histopathology',
            'serial imaging showing no change',
            'SINGLE IMAGE EXPERT CONSENSUS'
        ]:
            data = {'diagnosis_confirm_type': value}
            image = self._createImage()
            self.assertRunParser(image, data, parser)
            self.assertDictEqual({}, data)
            self.assertDictEqual({}, image['meta']['unstructured'])
            self.assertDictEqual(
                {'diagnosis_confirm_type': value.lower()},
                image['meta']['clinical'])
            self.assertDictEqual({}, image['privateMeta'])

        # Invalid value
        data = {'diagnosis_confirm_type': 'none'}
        image = self._createImage()
        self.assertRunParserRaises(image, data, parser, BadFieldTypeException)

        # Unknown values
        for value in self.unknownValues:
            data = {'diagnosis_confirm_type': value}
            image = self._createImage()
            self.assertRunParser(image, data, parser)
            self.assertDictEqual({}, data)
            self.assertDictEqual({}, image['meta']['unstructured'])
            self.assertDictEqual({'diagnosis_confirm_type': None}, image['meta']['clinical'])
            self.assertDictEqual({}, image['privateMeta'])

        # Update null value with new value
        data = {'diagnosis_confirm_type': 'histopathology'}
        image = self._createImage()
        image['meta']['clinical']['diagnosis_confirm_type'] = None
        self.assertRunParser(image, data, parser)
        self.assertDictEqual({}, data)
        self.assertDictEqual({}, image['meta']['unstructured'])
        self.assertDictEqual(
            {'diagnosis_confirm_type': 'histopathology'},
            image['meta']['clinical'])
        self.assertDictEqual({}, image['privateMeta'])

        # Update existing value with same value
        data = {'diagnosis_confirm_type': 'histopathology'}
        image = self._createImage()
        image['meta']['clinical']['diagnosis_confirm_type'] = 'histopathology'
        self.assertRunParser(image, data, parser)
        self.assertDictEqual({}, data)
        self.assertDictEqual({}, image['meta']['unstructured'])
        self.assertDictEqual(
            {'diagnosis_confirm_type': 'histopathology'},
            image['meta']['clinical'])
        self.assertDictEqual({}, image['privateMeta'])

        # Update existing value with null value
        data = {'diagnosis_confirm_type': None}
        image = self._createImage()
        image['meta']['clinical']['diagnosis_confirm_type'] = 'histopathology'
        self.assertRunParserRaises(image, data, parser, MetadataValueExistsException)

        # Update existing value with new value
        data = {'diagnosis_confirm_type': 'serial imaging showing no change'}
        image = self._createImage()
        image['meta']['clinical']['diagnosis_confirm_type'] = 'histopathology'
        self.assertRunParserRaises(image, data, parser, MetadataValueExistsException)

        # Field not found
        self._testFieldNotFound(parser)

        # Bad field type
        data = {'diagnosis_confirm_type': '1'}
        image = self._createImage()
        self.assertRunParserRaises(image, data, parser, BadFieldTypeException)

    def testBenignMalignantFieldParser(self):
        parser = BenignMalignantFieldParser

        # Valid values with varying case
        for value in [
            'benign',
            'malignant',
            'indeterminate',
            'indeterminate/benign',
            'indeterminate/malignant',
            'BENIGN',
            'INDETERMINATE/MALIGNANT'
        ]:
            data = {'benign_malignant': value}
            image = self._createImage()
            self.assertRunParser(image, data, parser)
            self.assertDictEqual({}, data)
            self.assertDictEqual({}, image['meta']['unstructured'])
            self.assertDictEqual({'benign_malignant': value.lower()}, image['meta']['clinical'])
            self.assertDictEqual({}, image['privateMeta'])

        # Autocorrected value
        data = {'benign_malignant': 'INDETERMINABLE'}
        image = self._createImage()
        self.assertRunParser(image, data, parser)
        self.assertDictEqual({}, data)
        self.assertDictEqual({}, image['meta']['unstructured'])
        self.assertDictEqual({'benign_malignant': 'indeterminate'}, image['meta']['clinical'])
        self.assertDictEqual({}, image['privateMeta'])

        # Invalid value
        data = {'benign_malignant': 'ok'}
        image = self._createImage()
        self.assertRunParserRaises(image, data, parser, BadFieldTypeException)

        # Alternative field name
        data = {'BEN_MAL': 'benign'}
        image = self._createImage()
        self.assertRunParser(image, data, parser)
        self.assertDictEqual({}, data)
        self.assertDictEqual({}, image['meta']['unstructured'])
        self.assertDictEqual({'benign_malignant': 'benign'}, image['meta']['clinical'])
        self.assertDictEqual({}, image['privateMeta'])

        # Unknown values
        for value in self.unknownValues:
            data = {'benign_malignant': value}
            image = self._createImage()
            self.assertRunParser(image, data, parser)
            self.assertDictEqual({}, data)
            self.assertDictEqual({}, image['meta']['unstructured'])
            self.assertDictEqual({'benign_malignant': None}, image['meta']['clinical'])
            self.assertDictEqual({}, image['privateMeta'])

        # Duplicate field
        data = {'benign_malignant': 'indeterminate', 'ben_mal': 'indeterminate'}
        image = self._createImage()
        self.assertRunParserRaises(image, data, parser, MultipleFieldException)

        # Update null value with new value
        data = {'benign_malignant': 'malignant'}
        image = self._createImage()
        image['meta']['clinical']['benign_malignant'] = None
        self.assertRunParser(image, data, parser)
        self.assertDictEqual({}, data)
        self.assertDictEqual({}, image['meta']['unstructured'])
        self.assertDictEqual({'benign_malignant': 'malignant'}, image['meta']['clinical'])
        self.assertDictEqual({}, image['privateMeta'])

        # Update existing value with same value
        data = {'benign_malignant': 'malignant'}
        image = self._createImage()
        image['meta']['clinical']['benign_malignant'] = 'malignant'
        self.assertRunParser(image, data, parser)
        self.assertDictEqual({}, data)
        self.assertDictEqual({}, image['meta']['unstructured'])
        self.assertDictEqual({'benign_malignant': 'malignant'}, image['meta']['clinical'])
        self.assertDictEqual({}, image['privateMeta'])

        # Update existing value with null value
        data = {'benign_malignant': None}
        image = self._createImage()
        image['meta']['clinical']['benign_malignant'] = 'malignant'
        self.assertRunParserRaises(image, data, parser, MetadataValueExistsException)

        # Update existing value with new value
        data = {'benign_malignant': 'malignant'}
        image = self._createImage()
        image['meta']['clinical']['benign_malignant'] = 'benign'
        self.assertRunParserRaises(image, data, parser, MetadataValueExistsException)

        # Field not found
        self._testFieldNotFound(parser)

        # Bad field type
        data = {'benign_malignant': '1'}
        image = self._createImage()
        self.assertRunParserRaises(image, data, parser, BadFieldTypeException)

    def testDiagnosisFieldParser(self):
        parser = DiagnosisFieldParser

        # Valid values with varying case
        for value in [
            'actinic keratosis',
            'atypical spitz tumor',
            'basal cell carcinoma',
            'dermatofibroma',
            'EPHELIS',
            'lentigo simplex',
            'melanoma',
            'nevus'
        ]:
            data = {'diagnosis': value}
            image = self._createImage()
            self.assertRunParser(image, data, parser)
            self.assertDictEqual({}, data)
            self.assertDictEqual({}, image['meta']['unstructured'])
            self.assertDictEqual({'diagnosis': value.lower()}, image['meta']['clinical'])
            self.assertDictEqual({}, image['privateMeta'])

        # Special case: AIMP
        data = {'diagnosis': 'AIMP'}
        image = self._createImage()
        self.assertRunParser(image, data, parser)
        self.assertDictEqual({}, data)
        self.assertDictEqual({}, image['meta']['unstructured'])
        self.assertDictEqual({'diagnosis': 'AIMP'}, image['meta']['clinical'])
        self.assertDictEqual({}, image['privateMeta'])

        # Special case: lentigo NOS
        data = {'diagnosis': 'lentigo NOS'}
        image = self._createImage()
        self.assertRunParser(image, data, parser)
        self.assertDictEqual({}, data)
        self.assertDictEqual({}, image['meta']['unstructured'])
        self.assertDictEqual({'diagnosis': 'lentigo NOS'}, image['meta']['clinical'])
        self.assertDictEqual({}, image['privateMeta'])

        # Special case: Cafe-au-lait
        data = {'diagnosis': u'caf\xe9-au-lait macule'}
        image = self._createImage()
        self.assertRunParser(image, data, parser)
        self.assertDictEqual({}, data)
        self.assertDictEqual({}, image['meta']['unstructured'])
        self.assertDictEqual({'diagnosis': 'cafe-au-lait macule'}, image['meta']['clinical'])
        self.assertDictEqual({}, image['privateMeta'])

        # Alternative field name
        data = {'path_diagnosis': 'melanoma'}
        image = self._createImage()
        self.assertRunParser(image, data, parser)
        self.assertDictEqual({}, data)
        self.assertDictEqual({}, image['meta']['unstructured'])
        self.assertDictEqual({'diagnosis': 'melanoma'}, image['meta']['clinical'])
        self.assertDictEqual({}, image['privateMeta'])

        # Invalid value
        data = {'diagnosis': 'bad'}
        image = self._createImage()
        self.assertRunParserRaises(image, data, parser, BadFieldTypeException)

        # Unknown values
        for value in self.unknownValues:
            data = {'diagnosis': value}
            image = self._createImage()
            self.assertRunParser(image, data, parser)
            self.assertDictEqual({}, data)
            self.assertDictEqual({}, image['meta']['unstructured'])
            self.assertDictEqual({'diagnosis': None}, image['meta']['clinical'])
            self.assertDictEqual({}, image['privateMeta'])

        # Duplicate field
        data = {'diagnosis': 'dermatofibroma', 'path_diagnosis': 'dermatofibroma'}
        image = self._createImage()
        self.assertRunParserRaises(image, data, parser, MultipleFieldException)

        # Update null value with new value
        data = {'diagnosis': 'dermatofibroma'}
        image = self._createImage()
        image['meta']['clinical']['diagnosis'] = None
        self.assertRunParser(image, data, parser)
        self.assertDictEqual({}, data)
        self.assertDictEqual({}, image['meta']['unstructured'])
        self.assertDictEqual({'diagnosis': 'dermatofibroma'}, image['meta']['clinical'])
        self.assertDictEqual({}, image['privateMeta'])

        # Update existing value with same value
        data = {'diagnosis': 'dermatofibroma'}
        image = self._createImage()
        image['meta']['clinical']['diagnosis'] = 'dermatofibroma'
        self.assertRunParser(image, data, parser)
        self.assertDictEqual({}, data)
        self.assertDictEqual({}, image['meta']['unstructured'])
        self.assertDictEqual({'diagnosis': 'dermatofibroma'}, image['meta']['clinical'])
        self.assertDictEqual({}, image['privateMeta'])

        # Update existing value with null value
        data = {'diagnosis': None}
        image = self._createImage()
        image['meta']['clinical']['diagnosis'] = 'dermatofibroma'
        self.assertRunParserRaises(image, data, parser, MetadataValueExistsException)

        # Update existing value with new value
        data = {'diagnosis': 'melanoma'}
        image = self._createImage()
        image['meta']['clinical']['diagnosis'] = 'dermatofibroma'
        self.assertRunParserRaises(image, data, parser, MetadataValueExistsException)

        # Field not found
        self._testFieldNotFound(parser)

        # Bad field type
        data = {'diagnosis': '1'}
        image = self._createImage()
        self.assertRunParserRaises(image, data, parser, BadFieldTypeException)

    def testImageTypeFieldParser(self):
        parser = ImageTypeFieldParser

        # Valid values with varying case
        for value in [
            'dermoscopic',
            'CLINICAL',
            'Overview'
        ]:
            data = {'image_type': value}
            image = self._createImage()
            self.assertRunParser(image, data, parser)
            self.assertDictEqual({}, data)
            self.assertDictEqual({}, image['meta']['unstructured'])
            self.assertDictEqual({'image_type': value.lower()}, image['meta']['acquisition'])
            self.assertDictEqual({}, image['privateMeta'])

        # Invalid value
        data = {'image_type': 'bad'}
        image = self._createImage()
        self.assertRunParserRaises(image, data, parser, BadFieldTypeException)

        # Unknown values
        for value in self.unknownValues:
            data = {'image_type': value}
            image = self._createImage()
            self.assertRunParser(image, data, parser)
            self.assertDictEqual({}, data)
            self.assertDictEqual({}, image['meta']['unstructured'])
            self.assertDictEqual({'image_type': None}, image['meta']['acquisition'])
            self.assertDictEqual({}, image['privateMeta'])

        # Update null value with new value
        data = {'image_type': 'dermoscopic'}
        image = self._createImage()
        image['meta']['acquisition']['image_type'] = None
        self.assertRunParser(image, data, parser)
        self.assertDictEqual({}, data)
        self.assertDictEqual({}, image['meta']['unstructured'])
        self.assertDictEqual({'image_type': 'dermoscopic'}, image['meta']['acquisition'])
        self.assertDictEqual({}, image['privateMeta'])

        # Update existing value with same value
        data = {'image_type': 'dermoscopic'}
        image = self._createImage()
        image['meta']['acquisition']['image_type'] = 'dermoscopic'
        self.assertRunParser(image, data, parser)
        self.assertDictEqual({}, data)
        self.assertDictEqual({}, image['meta']['unstructured'])
        self.assertDictEqual({'image_type': 'dermoscopic'}, image['meta']['acquisition'])
        self.assertDictEqual({}, image['privateMeta'])

        # Update existing value with null value
        data = {'image_type': None}
        image = self._createImage()
        image['meta']['acquisition']['image_type'] = 'dermoscopic'
        self.assertRunParserRaises(image, data, parser, MetadataValueExistsException)

        # Update existing value with new value
        data = {'image_type': 'clinical'}
        image = self._createImage()
        image['meta']['acquisition']['image_type'] = 'dermoscopic'
        self.assertRunParserRaises(image, data, parser, MetadataValueExistsException)

        # Field not found
        self._testFieldNotFound(parser)

    def testDermoscopicTypeFieldParser(self):
        parser = DermoscopicTypeFieldParser

        # Valid values with varying case
        for value in [
            'contact polarized',
            'CONTACT NON-POLARIZED',
            'Non-contact Polarized'
        ]:
            data = {'dermoscopic_type': value}
            image = self._createImage()
            self.assertRunParser(image, data, parser)
            self.assertDictEqual({}, data)
            self.assertDictEqual({}, image['meta']['unstructured'])
            self.assertDictEqual({'dermoscopic_type': value.lower()}, image['meta']['acquisition'])
            self.assertDictEqual({}, image['privateMeta'])

        # Special case
        data = {'dermoscopic_type': 'contact non polarized'}
        image = self._createImage()
        self.assertRunParser(image, data, parser)
        self.assertDictEqual({}, data)
        self.assertDictEqual({}, image['meta']['unstructured'])
        self.assertDictEqual({'dermoscopic_type': 'contact non-polarized'},
                             image['meta']['acquisition'])
        self.assertDictEqual({}, image['privateMeta'])

        data = {'dermoscopic_type': 'non contact polarized'}
        image = self._createImage()
        self.assertRunParser(image, data, parser)
        self.assertDictEqual({}, data)
        self.assertDictEqual({}, image['meta']['unstructured'])
        self.assertDictEqual({'dermoscopic_type': 'non-contact polarized'},
                             image['meta']['acquisition'])
        self.assertDictEqual({}, image['privateMeta'])

        # Invalid value
        data = {'dermoscopic_type': 'bad'}
        image = self._createImage()
        self.assertRunParserRaises(image, data, parser, BadFieldTypeException)

        # Unknown values
        for value in self.unknownValues:
            data = {'dermoscopic_type': value}
            image = self._createImage()
            self.assertRunParser(image, data, parser)
            self.assertDictEqual({}, data)
            self.assertDictEqual({}, image['meta']['unstructured'])
            self.assertDictEqual({'dermoscopic_type': None}, image['meta']['acquisition'])
            self.assertDictEqual({}, image['privateMeta'])

        # Update null value with new value
        data = {'dermoscopic_type': 'contact polarized'}
        image = self._createImage()
        image['meta']['acquisition']['dermoscopic_type'] = None
        self.assertRunParser(image, data, parser)
        self.assertDictEqual({}, data)
        self.assertDictEqual({}, image['meta']['unstructured'])
        self.assertDictEqual({'dermoscopic_type': 'contact polarized'},
                             image['meta']['acquisition'])
        self.assertDictEqual({}, image['privateMeta'])

        # Update existing value with same value
        data = {'dermoscopic_type': 'contact polarized'}
        image = self._createImage()
        image['meta']['acquisition']['dermoscopic_type'] = 'contact polarized'
        self.assertRunParser(image, data, parser)
        self.assertDictEqual({}, data)
        self.assertDictEqual({}, image['meta']['unstructured'])
        self.assertDictEqual({'dermoscopic_type': 'contact polarized'},
                             image['meta']['acquisition'])
        self.assertDictEqual({}, image['privateMeta'])

        # Update existing value with null value
        data = {'dermoscopic_type': None}
        image = self._createImage()
        image['meta']['acquisition']['dermoscopic_type'] = 'contact polarized'
        self.assertRunParserRaises(image, data, parser, MetadataValueExistsException)

        # Update existing value with new value
        data = {'dermoscopic_type': 'contact non-polarized'}
        image = self._createImage()
        image['meta']['acquisition']['dermoscopic_type'] = 'contact polarized'
        self.assertRunParserRaises(image, data, parser, MetadataValueExistsException)

        # Field not found
        self._testFieldNotFound(parser)

    def testMelThickMmFieldParser(self):
        parser = MelThickMmFieldParser

        # Normal
        for value in ['1.23 mm', '1.23mm', '1.23']:
            data = {'mel_thick_mm': value}
            image = self._createImage()
            self.assertRunParser(image, data, parser)
            self.assertDictEqual({}, data)
            self.assertDictEqual({}, image['meta']['unstructured'])
            self.assertDictEqual({'mel_thick_mm': 1.23}, image['meta']['clinical'])
            self.assertDictEqual({}, image['privateMeta'])

        # Alternative field name
        data = {'mel_thick': '1.25 mm'}
        image = self._createImage()
        self.assertRunParser(image, data, parser)
        self.assertDictEqual({}, data)
        self.assertDictEqual({}, image['meta']['unstructured'])
        self.assertDictEqual({'mel_thick_mm': 1.25}, image['meta']['clinical'])
        self.assertDictEqual({}, image['privateMeta'])

        # Unknown values
        for value in self.unknownValues:
            data = {'mel_thick_mm': value}
            image = self._createImage()
            self.assertRunParser(image, data, parser)
            self.assertDictEqual({}, data)
            self.assertDictEqual({}, image['meta']['unstructured'])
            self.assertDictEqual({'mel_thick_mm': None}, image['meta']['clinical'])
            self.assertDictEqual({}, image['privateMeta'])

        # Update null value with new value
        data = {'mel_thick_mm': '1.23 mm'}
        image = self._createImage()
        image['meta']['clinical']['mel_thick_mm'] = None
        self.assertRunParser(image, data, parser)
        self.assertDictEqual({}, data)
        self.assertDictEqual({}, image['meta']['unstructured'])
        self.assertDictEqual({'mel_thick_mm': 1.23}, image['meta']['clinical'])
        self.assertDictEqual({}, image['privateMeta'])

        # Update existing value with same value
        data = {'mel_thick_mm': '1.23 mm'}
        image = self._createImage()
        image['meta']['clinical']['mel_thick_mm'] = 1.23
        self.assertRunParser(image, data, parser)
        self.assertDictEqual({}, data)
        self.assertDictEqual({}, image['meta']['unstructured'])
        self.assertDictEqual({'mel_thick_mm': 1.23}, image['meta']['clinical'])
        self.assertDictEqual({}, image['privateMeta'])

        # Update existing value with null value
        data = {'mel_thick_mm': None}
        image = self._createImage()
        image['meta']['clinical']['mel_thick_mm'] = 1.23
        self.assertRunParserRaises(image, data, parser, MetadataValueExistsException)

        # Update existing value with new value
        data = {'mel_thick_mm': '1.23 mm'}
        image = self._createImage()
        image['meta']['clinical']['mel_thick_mm'] = 2.1
        self.assertRunParserRaises(image, data, parser, MetadataValueExistsException)

        # Field not found
        self._testFieldNotFound(parser)

        # Bad field type
        data = {'mel_thick_mm': 'true'}
        image = self._createImage()
        self.assertRunParserRaises(image, data, parser, BadFieldTypeException)

        data = {'mel_thick_mm': '1.23 cm'}
        image = self._createImage()
        self.assertRunParserRaises(image, data, parser, BadFieldTypeException)

    def testMelClassFieldParser(self):
        parser = MelClassFieldParser

        # Valid values with varying case
        for value in [
            'melanoma in situ',
            'invasive melanoma',
            'recurrent/persistent melanoma, in situ',
            'RECURRENT/PERSISTENT MELANOMA, INVASIVE',
        ]:
            data = {'mel_class': value}
            image = self._createImage()
            self.assertRunParser(image, data, parser)
            self.assertDictEqual({}, data)
            self.assertDictEqual({}, image['meta']['unstructured'])
            self.assertDictEqual({'mel_class': value.lower()}, image['meta']['clinical'])
            self.assertDictEqual({}, image['privateMeta'])

        # Special case
        data = {'mel_class': 'recurrent/persistent melanoma in situ'}
        image = self._createImage()
        self.assertRunParser(image, data, parser)
        self.assertDictEqual({}, data)
        self.assertDictEqual({}, image['meta']['unstructured'])
        self.assertDictEqual({'mel_class': 'recurrent/persistent melanoma, in situ'},
                             image['meta']['clinical'])
        self.assertDictEqual({}, image['privateMeta'])

        # Special case
        data = {'mel_class': 'recurrent/persistent melanoma invasive'}
        image = self._createImage()
        self.assertRunParser(image, data, parser)
        self.assertDictEqual({}, data)
        self.assertDictEqual({}, image['meta']['unstructured'])
        self.assertDictEqual({'mel_class': 'recurrent/persistent melanoma, invasive'},
                             image['meta']['clinical'])
        self.assertDictEqual({}, image['privateMeta'])

        # Special case
        data = {'mel_class': 'melanoma nos'}
        image = self._createImage()
        self.assertRunParser(image, data, parser)
        self.assertDictEqual({}, data)
        self.assertDictEqual({}, image['meta']['unstructured'])
        self.assertDictEqual({'mel_class': 'melanoma NOS'},
                             image['meta']['clinical'])
        self.assertDictEqual({}, image['privateMeta'])

        # Invalid value
        data = {'mel_class': 'bad'}
        image = self._createImage()
        self.assertRunParserRaises(image, data, parser, BadFieldTypeException)

        # Unknown values
        for value in self.unknownValues:
            data = {'mel_class': value}
            image = self._createImage()
            self.assertRunParser(image, data, parser)
            self.assertDictEqual({}, data)
            self.assertDictEqual({}, image['meta']['unstructured'])
            self.assertDictEqual({'mel_class': None}, image['meta']['clinical'])
            self.assertDictEqual({}, image['privateMeta'])

        # Update null value with new value
        data = {'mel_class': 'melanoma in situ'}
        image = self._createImage()
        image['meta']['clinical']['mel_class'] = None
        self.assertRunParser(image, data, parser)
        self.assertDictEqual({}, data)
        self.assertDictEqual({}, image['meta']['unstructured'])
        self.assertDictEqual({'mel_class': 'melanoma in situ'},
                             image['meta']['clinical'])
        self.assertDictEqual({}, image['privateMeta'])

        # Update existing value with same value
        data = {'mel_class': 'melanoma in situ'}
        image = self._createImage()
        image['meta']['clinical']['mel_class'] = 'melanoma in situ'
        self.assertRunParser(image, data, parser)
        self.assertDictEqual({}, data)
        self.assertDictEqual({}, image['meta']['unstructured'])
        self.assertDictEqual({'mel_class': 'melanoma in situ'},
                             image['meta']['clinical'])
        self.assertDictEqual({}, image['privateMeta'])

        # Update existing value with null value
        data = {'mel_class': None}
        image = self._createImage()
        image['meta']['clinical']['mel_class'] = 'melanoma in situ'
        self.assertRunParserRaises(image, data, parser, MetadataValueExistsException)

        # Update existing value with new value
        data = {'mel_class': 'melanoma nos'}
        image = self._createImage()
        image['meta']['clinical']['mel_class'] = 'melanoma in situ'
        self.assertRunParserRaises(image, data, parser, MetadataValueExistsException)

        # Field not found
        self._testFieldNotFound(parser)

    def testAddImageClinicalMetadata(self):
        # Empty data
        data = {}
        image = self._createImage()
        errors, unrecognizedFields = addImageMetadata(image, data)
        self.assertEquals([], errors)
        self.assertEquals(0, len(unrecognizedFields))

        # Valid data with unrecognized fields and existing metadata
        data = {
            'age': '45',
            'family_hx_mm': 'false',
            'personal_hx_mm': 'false',
            'clin_size_long_diam_mm': '3.0 mm',
            'melanocytic': 'true',
            'diagnosis_confirm_type': 'histopathology',
            'benign_malignant': 'malignant',
            'diagnosis': 'melanoma',
            'anatom_site_general': 'head',
            'anatomic': 'neck'
        }
        image = self._createImage()
        image['meta']['clinical']['sex'] = 'female'
        image['meta']['unstructured']['laterality'] = 'left'
        errors, warnings = addImageMetadata(image, data)
        self.assertEquals([], errors)
        self.assertDictEqual({
            'anatom_site_general': 'head',
            'anatomic': 'neck',
            'laterality': 'left'
        }, image['meta']['unstructured'])
        self.assertDictEqual({
            'age_approx': 45,
            'sex': 'female',
            'family_hx_mm': False,
            'personal_hx_mm': False,
            'clin_size_long_diam_mm': 3.0,
            'melanocytic': True,
            'diagnosis_confirm_type': 'histopathology',
            'benign_malignant': 'malignant',
            'diagnosis': 'melanoma',
        }, image['meta']['clinical'])
        self.assertDictEqual({
            'age': 45
        }, image['privateMeta'])
        self.assertEquals(2, len(warnings))
        self.assertIn(
            "unrecognized field 'anatomic' will be added to unstructured metadata",
            warnings)
        self.assertIn(
            "unrecognized field 'anatom_site_general' will be added to unstructured metadata",
            warnings)

        # Data with errors
        data = {
            'age': '45',
            'sex': 'female',
            'family_hx_mm': 'false',
            'personal_hx_mm': 'false',
            'clin_size_long_diam_mm': '3.0+',
            'melanocytic': None,
            'diagnosis_confirm_type': 'histopathology',
            'benign_malignant': 'malignant',
            'ben_mal': 'malignant',
            'diagnosis': 'melanoma',
            'anatom_site_general': 'head',
            'anatomic': 'neck'
        }
        image = self._createImage()
        image['meta']['clinical']['sex'] = 'male'
        image['meta']['clinical']['melanocytic'] = False
        errors, warnings = addImageMetadata(image, data)
        self.assertEquals(5, len(errors))
        self.assertIn(
            "value already exists for field 'sex' (old: 'male', new: 'female')",
            errors)
        self.assertIn(
            "value is wrong type for field 'clin_size_long_diam_mm' "
            "(expected 'float with units (um, mm, or cm)', value: '3.0+')",
            errors)
        self.assertIn(
            "value already exists for field 'melanocytic' (old: False, new: None)",
            errors)
        self.assertIn(
            "only one of field 'benign_malignant' may be present, "
            "found: ['ben_mal', 'benign_malignant']",
            errors)
        self.assertIn(
            "values ['melanoma', False] for fields ['diagnosis', 'melanocytic'] are inconsistent",
            errors)
        self.assertEquals([], warnings)

    def testAddImageClinicalMetadataInterfieldValidation(self):
        # Valid cases
        data = {
            'benign_malignant': None,
            'diagnosis': 'melanoma',
            'diagnosis_confirm_type': 'histopathology'
        }
        image = self._createImage()
        errors, _ = addImageMetadata(image, data)
        self.assertEqual([], errors)
        self.assertEqual('malignant', image['meta']['clinical']['benign_malignant'])

        data = {
            'benign_malignant': None,
            'diagnosis': 'nevus',
            'diagnosis_confirm_type': 'single image expert consensus'
        }
        image = self._createImage()
        errors, _ = addImageMetadata(image, data)
        self.assertEqual([], errors)
        self.assertEqual('benign', image['meta']['clinical']['benign_malignant'])

        data = {
            'benign_malignant': 'indeterminate',
            'diagnosis': 'other',
            'diagnosis_confirm_type': 'histopathology'
        }
        image = self._createImage()
        errors, _ = addImageMetadata(image, data)
        self.assertEqual([], errors)

        data = {
            'image_type': 'dermoscopic',
            'dermoscopic_type': 'contact polarized'
        }
        image = self._createImage()
        errors, _ = addImageMetadata(image, data)
        self.assertEqual([], errors)

        data = {
            'image_type': 'clinical',
            'dermoscopic_type': None
        }
        image = self._createImage()
        errors, _ = addImageMetadata(image, data)
        self.assertEqual([], errors)

        data = {
            'image_type': None,
            'dermoscopic_type': 'contact non-polarized'
        }
        image = self._createImage()
        errors, _ = addImageMetadata(image, data)
        self.assertEqual([], errors)
        self.assertEqual('dermoscopic', image['meta']['acquisition']['image_type'])

        # Error cases
        data = {
            'benign_malignant': 'benign',
            'diagnosis': 'melanoma',
        }
        image = self._createImage()
        errors, _ = addImageMetadata(image, data)
        self.assertEqual(1, len(errors))

        data = {
            'benign_malignant': 'malignant',
            'diagnosis': 'nevus',
        }
        image = self._createImage()
        errors, _ = addImageMetadata(image, data)
        self.assertEqual(1, len(errors))

        data = {
            'benign_malignant': 'indeterminate',
            'diagnosis': 'other',
            'diagnosis_confirm_type': 'single image expert consensus'
        }
        image = self._createImage()
        errors, _ = addImageMetadata(image, data)
        self.assertEqual(1, len(errors))

        data = {
            'image_type': 'clinical',
            'dermoscopic_type': 'contact polarized'
        }
        image = self._createImage()
        errors, _ = addImageMetadata(image, data)
        self.assertEqual(1, len(errors))

        # Warning cases
        data = {
            'benign_malignant': 'benign',
            'diagnosis': 'basal cell carcinoma',
        }
        image = self._createImage()
        errors, warnings = addImageMetadata(image, data)
        self.assertEqual([], errors)
        self.assertEqual(1, len(warnings))
