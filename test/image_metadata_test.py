import pytest

from isic_archive.models.dataset_helpers.image_metadata import (
    addImageMetadata,
    AgeFieldParser,
    BadFieldTypeException,
    BenignMalignantFieldParser,
    ClinicalSizeFieldParser,
    DermoscopicTypeFieldParser,
    DiagnosisConfirmTypeFieldParser,
    DiagnosisFieldParser,
    FamilyHxMmFieldParser,
    GeneralAnatomicSiteFieldParser,
    ImageTypeFieldParser,
    LesionIdFieldParser,
    MelanocyticFieldParser,
    MelClassFieldParser,
    MelMitoticIndexFieldParser,
    MelThickMmFieldParser,
    MelTypeFieldParser,
    MelUlcerFieldParser,
    MetadataValueExistsException,
    MultipleFieldException,
    NevusTypeFieldParser,
    PatientIdFieldParser,
    PersonalHxMmFieldParser,
    SexFieldParser,
)

unknownValues = [None, '', 'unknown', 'UNKNOWN']


def _createImage():
    """Create an empty mock image object."""
    image = {
        'meta': {
            'acquisition': {},
            'clinical': {},
            'unstructured': {},
            'unstructuredExif': {}
        },
        'privateMeta': {}
    }
    return image


def _runParser(image, data, parser):
    acquisition = image['meta']['acquisition']
    clinical = image['meta']['clinical']
    private = image['privateMeta']
    parser.run(data, acquisition, clinical, private)


def assertRunParserRaises(image, data, parser, exception):
    """Assert that running the parser raises the specified exception type."""
    with pytest.raises(exception):
        _runParser(image, data, parser)


def _testFieldNotFound(parser):
    """
    Test that a parser makes no changes if none of its allowed fields are given in the metadata.

    This is a convenience method.
    """
    data = {'other': 'value'}
    image = _createImage()
    _runParser(image, data, parser)
    assert {'other': 'value'} == data
    assert {} == image['meta']['acquisition']
    assert {} == image['meta']['clinical']
    assert {} == image['meta']['unstructured']
    assert {} == image['privateMeta']


def testAgeFieldParser():
    parser = AgeFieldParser

    # Multiple of 5
    data = {'age': '25'}
    image = _createImage()
    _runParser(image, data, parser)
    assert {} == data
    assert {} == image['meta']['unstructured']
    assert {'age_approx': 25} == image['meta']['clinical']
    assert {'age': 25} == image['privateMeta']

    # Not a multiple of 5
    data = {'age': '38'}
    image = _createImage()
    _runParser(image, data, parser)
    assert {} == data
    assert {} == image['meta']['unstructured']
    assert {'age_approx': 40} == image['meta']['clinical']
    assert {'age': 38} == image['privateMeta']

    # Special maximum value
    data = {'age': '85+'}
    image = _createImage()
    _runParser(image, data, parser)
    assert {} == data
    assert {} == image['meta']['unstructured']
    assert {'age_approx': 85} == image['meta']['clinical']
    assert {'age': 85} == image['privateMeta']

    # Greater than maximum
    data = {'age': '86'}
    image = _createImage()
    _runParser(image, data, parser)
    assert {} == data
    assert {} == image['meta']['unstructured']
    assert {'age_approx': 85} == image['meta']['clinical']
    assert {'age': 85} == image['privateMeta']

    # Mixed case field name
    data = {'Age': '25'}
    image = _createImage()
    _runParser(image, data, parser)
    assert {} == data
    assert {} == image['meta']['unstructured']
    assert {'age_approx': 25} == image['meta']['clinical']
    assert {'age': 25} == image['privateMeta']

    # Unknown values
    for value in unknownValues:
        data = {'age': value}
        image = _createImage()
        _runParser(image, data, parser)
        assert {} == data
        assert {} == image['meta']['unstructured']
        assert {'age_approx': None} == image['meta']['clinical']
        assert {'age': None} == image['privateMeta']

    # Update null value with new value
    data = {'age': '25'}
    image = _createImage()
    image['meta']['clinical'] = {'age_approx': None}
    image['privateMeta']['age'] = None
    _runParser(image, data, parser)
    assert {} == data
    assert {} == image['meta']['unstructured']
    assert {'age_approx': 25} == image['meta']['clinical']
    assert {'age': 25} == image['privateMeta']

    # Update existing value with same value
    data = {'age': '25'}
    image = _createImage()
    image['meta']['clinical']['age_approx'] = 25
    image['privateMeta']['age'] = 25
    _runParser(image, data, parser)
    assert {} == data
    assert {} == image['meta']['unstructured']
    assert {'age_approx': 25} == image['meta']['clinical']
    assert {'age': 25} == image['privateMeta']

    # Update existing value with null value
    data = {'age': None}
    image = _createImage()
    image['meta']['clinical']['age_approx'] = 25
    image['privateMeta']['age'] = 25
    assertRunParserRaises(image, data, parser, MetadataValueExistsException)

    # Update existing value with new value
    data = {'age': '50'}
    image = _createImage()
    image['meta']['clinical']['age_approx'] = 25
    image['privateMeta']['age'] = 25
    assertRunParserRaises(image, data, parser, MetadataValueExistsException)

    # Field not found
    _testFieldNotFound(parser)

    # Bad field type
    data = {'age': 'true'}
    image = _createImage()
    assertRunParserRaises(image, data, parser, BadFieldTypeException)


def testSexFieldParser():
    parser = SexFieldParser

    # Abbreviation, lowercase
    data = {'sex': 'f'}
    image = _createImage()
    _runParser(image, data, parser)
    assert {} == data
    assert {} == image['meta']['unstructured']
    assert {'sex': 'female'} == image['meta']['clinical']
    assert {} == image['privateMeta']

    # Abbreviation, uppercase
    data = {'sex': 'M'}
    image = _createImage()
    _runParser(image, data, parser)
    assert {} == data
    assert {} == image['meta']['unstructured']
    assert {'sex': 'male'} == image['meta']['clinical']
    assert {} == image['privateMeta']

    # Unabbreviated, mixed case
    data = {'sex': 'Female'}
    image = _createImage()
    _runParser(image, data, parser)
    assert {} == data
    assert {} == image['meta']['unstructured']
    assert {'sex': 'female'} == image['meta']['clinical']
    assert {} == image['privateMeta']

    # Alternative field name
    data = {'gender': 'f'}
    image = _createImage()
    _runParser(image, data, parser)
    assert {} == data
    assert {} == image['meta']['unstructured']
    assert {'sex': 'female'} == image['meta']['clinical']
    assert {} == image['privateMeta']

    # Mixed case field name
    data = {'Gender': 'f'}
    image = _createImage()
    _runParser(image, data, parser)
    assert {} == data
    assert {} == image['meta']['unstructured']
    assert {'sex': 'female'} == image['meta']['clinical']
    assert {} == image['privateMeta']

    # Unknown values
    for value in unknownValues:
        data = {'sex': value}
        image = _createImage()
        _runParser(image, data, parser)
        assert {} == data
        assert {} == image['meta']['unstructured']
        assert {'sex': None} == image['meta']['clinical']
        assert {} == image['privateMeta']

    # Duplicate field
    data = {'gender': 'f', 'sex': 'f'}
    image = _createImage()
    assertRunParserRaises(image, data, parser, MultipleFieldException)

    # Update null value with new value
    data = {'gender': 'f'}
    image = _createImage()
    image['meta']['clinical']['sex'] = None
    _runParser(image, data, parser)
    assert {} == data
    assert {} == image['meta']['unstructured']
    assert {'sex': 'female'} == image['meta']['clinical']
    assert {} == image['privateMeta']

    # Update existing value with same value
    data = {'gender': 'f'}
    image = _createImage()
    image['meta']['clinical']['sex'] = 'female'
    _runParser(image, data, parser)
    assert {} == data
    assert {} == image['meta']['unstructured']
    assert {'sex': 'female'} == image['meta']['clinical']
    assert {} == image['privateMeta']

    # Update existing value with null value
    data = {'gender': None}
    image = _createImage()
    image['meta']['clinical']['sex'] = 'female'
    assertRunParserRaises(image, data, parser, MetadataValueExistsException)

    # Update existing value with new value
    data = {'gender': 'm'}
    image = _createImage()
    image['meta']['clinical']['sex'] = 'female'
    assertRunParserRaises(image, data, parser, MetadataValueExistsException)

    # Field not found
    _testFieldNotFound(parser)

    # Bad field type
    data = {'sex': 'true'}
    image = _createImage()
    assertRunParserRaises(image, data, parser, BadFieldTypeException)


def testFamilyHxMmFieldParser():
    parser = FamilyHxMmFieldParser

    # Standard field name
    data = {'family_hx_mm': 'true'}
    image = _createImage()
    _runParser(image, data, parser)
    assert {} == data
    assert {} == image['meta']['unstructured']
    assert {'family_hx_mm': True} == image['meta']['clinical']
    assert {} == image['privateMeta']

    # Alternative field name
    data = {'FamHxMM': 'true'}
    image = _createImage()
    _runParser(image, data, parser)
    assert {} == data
    assert {} == image['meta']['unstructured']
    assert {'family_hx_mm': True} == image['meta']['clinical']
    assert {} == image['privateMeta']

    # Unknown values
    for value in unknownValues:
        data = {'family_hx_mm': value}
        image = _createImage()
        _runParser(image, data, parser)
        assert {} == data
        assert {} == image['meta']['unstructured']
        assert {'family_hx_mm': None} == image['meta']['clinical']
        assert {} == image['privateMeta']

    # Duplicate field
    data = {'family_hx_mm': 'false', 'FamHxMM': 'false'}
    image = _createImage()
    assertRunParserRaises(image, data, parser, MultipleFieldException)

    # Update null value with new value
    data = {'family_hx_mm': 'false'}
    image = _createImage()
    image['meta']['clinical']['family_hx_mm'] = None
    _runParser(image, data, parser)
    assert {} == data
    assert {} == image['meta']['unstructured']
    assert {'family_hx_mm': False} == image['meta']['clinical']
    assert {} == image['privateMeta']

    # Update existing value with same value
    data = {'family_hx_mm': 'false'}
    image = _createImage()
    image['meta']['clinical']['family_hx_mm'] = False
    _runParser(image, data, parser)
    assert {} == data
    assert {} == image['meta']['unstructured']
    assert {'family_hx_mm': False} == image['meta']['clinical']
    assert {} == image['privateMeta']

    # Update existing value with null value
    data = {'family_hx_mm': None}
    image = _createImage()
    image['meta']['clinical']['family_hx_mm'] = False
    assertRunParserRaises(image, data, parser, MetadataValueExistsException)

    # Update existing value with new value
    data = {'family_hx_mm': 'true'}
    image = _createImage()
    image['meta']['clinical']['family_hx_mm'] = False
    assertRunParserRaises(image, data, parser, MetadataValueExistsException)

    # Field not found
    _testFieldNotFound(parser)

    # Bad field type
    data = {'family_hx_mm': '1'}
    image = _createImage()
    assertRunParserRaises(image, data, parser, BadFieldTypeException)


def testPersonalHxMmFieldParser():
    parser = PersonalHxMmFieldParser

    # Normal
    data = {'personal_hx_mm': 'true'}
    image = _createImage()
    _runParser(image, data, parser)
    assert {} == data
    assert {} == image['meta']['unstructured']
    assert {'personal_hx_mm': True} == image['meta']['clinical']
    assert {} == image['privateMeta']

    # Normal, alternative value representation
    data = {'personal_hx_mm': 'no'}
    image = _createImage()
    _runParser(image, data, parser)
    assert {} == data
    assert {} == image['meta']['unstructured']
    assert {'personal_hx_mm': False} == image['meta']['clinical']
    assert {} == image['privateMeta']

    # Unknown values
    for value in unknownValues:
        data = {'personal_hx_mm': value}
        image = _createImage()
        _runParser(image, data, parser)
        assert {} == data
        assert {} == image['meta']['unstructured']
        assert {'personal_hx_mm': None} == image['meta']['clinical']
        assert {} == image['privateMeta']

    # Update null value with new value
    data = {'personal_hx_mm': 'false'}
    image = _createImage()
    image['meta']['clinical']['personal_hx_mm'] = None
    _runParser(image, data, parser)
    assert {} == data
    assert {} == image['meta']['unstructured']
    assert {'personal_hx_mm': False} == image['meta']['clinical']
    assert {} == image['privateMeta']

    # Update existing value with same value
    data = {'personal_hx_mm': 'false'}
    image = _createImage()
    image['meta']['clinical']['personal_hx_mm'] = False
    _runParser(image, data, parser)
    assert {} == data
    assert {} == image['meta']['unstructured']
    assert {'personal_hx_mm': False} == image['meta']['clinical']
    assert {} == image['privateMeta']

    # Update existing value with null value
    data = {'personal_hx_mm': None}
    image = _createImage()
    image['meta']['clinical']['personal_hx_mm'] = False
    assertRunParserRaises(image, data, parser, MetadataValueExistsException)

    # Update existing value with new value
    data = {'personal_hx_mm': 'true'}
    image = _createImage()
    image['meta']['clinical']['personal_hx_mm'] = False
    assertRunParserRaises(image, data, parser, MetadataValueExistsException)

    # Field not found
    _testFieldNotFound(parser)

    # Bad field type
    data = {'personal_hx_mm': '1'}
    image = _createImage()
    assertRunParserRaises(image, data, parser, BadFieldTypeException)


def testClinicalSizeFieldParser():
    parser = ClinicalSizeFieldParser

    # Normal, um
    data = {'clin_size_long_diam_mm': '1500.0 um'}
    image = _createImage()
    _runParser(image, data, parser)
    assert {} == data
    assert {} == image['meta']['unstructured']
    assert {'clin_size_long_diam_mm': 1.5} == image['meta']['clinical']
    assert {} == image['privateMeta']

    # Normal, mm
    data = {'clin_size_long_diam_mm': '1.5 mm'}
    image = _createImage()
    _runParser(image, data, parser)
    assert {} == data
    assert {} == image['meta']['unstructured']
    assert {'clin_size_long_diam_mm': 1.5} == image['meta']['clinical']
    assert {} == image['privateMeta']

    # Normal, cm
    data = {'clin_size_long_diam_mm': '1.5 cm'}
    image = _createImage()
    _runParser(image, data, parser)
    assert {} == data
    assert {} == image['meta']['unstructured']
    assert {'clin_size_long_diam_mm': 15.0} == image['meta']['clinical']
    assert {} == image['privateMeta']

    # Unknown values
    for value in unknownValues:
        data = {'clin_size_long_diam_mm': value}
        image = _createImage()
        _runParser(image, data, parser)
        assert {} == data
        assert {} == image['meta']['unstructured']
        assert {'clin_size_long_diam_mm': None} == image['meta']['clinical']
        assert {} == image['privateMeta']

    # Update null value with new value
    data = {'clin_size_long_diam_mm': '1.5 mm'}
    image = _createImage()
    image['meta']['clinical']['clin_size_long_diam_mm'] = None
    _runParser(image, data, parser)
    assert {} == data
    assert {} == image['meta']['unstructured']
    assert {'clin_size_long_diam_mm': 1.5} == image['meta']['clinical']
    assert {} == image['privateMeta']

    # Update existing value with same value
    data = {'clin_size_long_diam_mm': '1.5 mm'}
    image = _createImage()
    image['meta']['clinical']['clin_size_long_diam_mm'] = 1.5
    _runParser(image, data, parser)
    assert {} == data
    assert {} == image['meta']['unstructured']
    assert {'clin_size_long_diam_mm': 1.5} == image['meta']['clinical']
    assert {} == image['privateMeta']

    # Update existing value with null value
    data = {'clin_size_long_diam_mm': None}
    image = _createImage()
    image['meta']['clinical']['clin_size_long_diam_mm'] = 1.5
    assertRunParserRaises(image, data, parser, MetadataValueExistsException)

    # Update existing value with new value
    data = {'clin_size_long_diam_mm': '1.5 mm'}
    image = _createImage()
    image['meta']['clinical']['clin_size_long_diam_mm'] = 2.0
    assertRunParserRaises(image, data, parser, MetadataValueExistsException)

    # Field not found
    _testFieldNotFound(parser)

    # Bad field type
    data = {'clin_size_long_diam_mm': 'true'}
    image = _createImage()
    assertRunParserRaises(image, data, parser, BadFieldTypeException)

    data = {'clin_size_long_diam_mm': '0.001 m'}
    image = _createImage()
    assertRunParserRaises(image, data, parser, BadFieldTypeException)

    data = {'clin_size_long_diam_mm': 'inf'}
    image = _createImage()
    assertRunParserRaises(image, data, parser, BadFieldTypeException)

    data = {'clin_size_long_diam_mm': 'inf mm'}
    image = _createImage()
    assertRunParserRaises(image, data, parser, BadFieldTypeException)


def testMelanocyticFieldParser():
    parser = MelanocyticFieldParser

    # Normal
    data = {'melanocytic': 'false'}
    image = _createImage()
    _runParser(image, data, parser)
    assert {} == data
    assert {} == image['meta']['unstructured']
    assert {'melanocytic': False} == image['meta']['clinical']
    assert {} == image['privateMeta']

    # Unknown values
    for value in unknownValues:
        data = {'melanocytic': value}
        image = _createImage()
        _runParser(image, data, parser)
        assert {} == data
        assert {} == image['meta']['unstructured']
        assert {'melanocytic': None} == image['meta']['clinical']
        assert {} == image['privateMeta']

    # Update null value with new value
    data = {'melanocytic': 'true'}
    image = _createImage()
    image['meta']['clinical']['melanocytic'] = None
    _runParser(image, data, parser)
    assert {} == data
    assert {} == image['meta']['unstructured']
    assert {'melanocytic': True} == image['meta']['clinical']
    assert {} == image['privateMeta']

    # Update existing value with same value
    data = {'melanocytic': 'true'}
    image = _createImage()
    image['meta']['clinical']['melanocytic'] = True
    _runParser(image, data, parser)
    assert {} == data
    assert {} == image['meta']['unstructured']
    assert {'melanocytic': True} == image['meta']['clinical']
    assert {} == image['privateMeta']

    # Update existing value with null value
    data = {'melanocytic': None}
    image = _createImage()
    image['meta']['clinical']['melanocytic'] = True
    assertRunParserRaises(image, data, parser, MetadataValueExistsException)

    # Update existing value with new value
    data = {'melanocytic': 'true'}
    image = _createImage()
    image['meta']['clinical']['melanocytic'] = False
    assertRunParserRaises(image, data, parser, MetadataValueExistsException)

    # Field not found
    _testFieldNotFound(parser)

    # Bad field type
    data = {'melanocytic': '1'}
    image = _createImage()
    assertRunParserRaises(image, data, parser, BadFieldTypeException)


def testDiagnosisConfirmTypeFieldParser():
    parser = DiagnosisConfirmTypeFieldParser

    # Valid values with varying case
    for value in [
        'histopathology',
        'serial imaging showing no change',
        'SINGLE IMAGE EXPERT CONSENSUS',
        '  confocal microscopy WITH consensus dermoscopy  '
    ]:
        data = {'diagnosis_confirm_type': value}
        image = _createImage()
        _runParser(image, data, parser)
        assert {} == data
        assert {} == image['meta']['unstructured']
        assert {'diagnosis_confirm_type': value.strip().lower()} == \
            image['meta']['clinical']
        assert {} == image['privateMeta']

    # Invalid value
    data = {'diagnosis_confirm_type': 'none'}
    image = _createImage()
    assertRunParserRaises(image, data, parser, BadFieldTypeException)

    # Unknown values
    for value in unknownValues:
        data = {'diagnosis_confirm_type': value}
        image = _createImage()
        _runParser(image, data, parser)
        assert {} == data
        assert {} == image['meta']['unstructured']
        assert {'diagnosis_confirm_type': None} == image['meta']['clinical']
        assert {} == image['privateMeta']

    # Update null value with new value
    data = {'diagnosis_confirm_type': 'histopathology'}
    image = _createImage()
    image['meta']['clinical']['diagnosis_confirm_type'] = None
    _runParser(image, data, parser)
    assert {} == data
    assert {} == image['meta']['unstructured']
    assert {'diagnosis_confirm_type': 'histopathology'} == \
        image['meta']['clinical']
    assert {} == image['privateMeta']

    # Update existing value with same value
    data = {'diagnosis_confirm_type': 'histopathology'}
    image = _createImage()
    image['meta']['clinical']['diagnosis_confirm_type'] = 'histopathology'
    _runParser(image, data, parser)
    assert {} == data
    assert {} == image['meta']['unstructured']
    assert {'diagnosis_confirm_type': 'histopathology'} == \
        image['meta']['clinical']
    assert {} == image['privateMeta']

    # Update existing value with null value
    data = {'diagnosis_confirm_type': None}
    image = _createImage()
    image['meta']['clinical']['diagnosis_confirm_type'] = 'histopathology'
    assertRunParserRaises(image, data, parser, MetadataValueExistsException)

    # Update existing value with new value
    data = {'diagnosis_confirm_type': 'serial imaging showing no change'}
    image = _createImage()
    image['meta']['clinical']['diagnosis_confirm_type'] = 'histopathology'
    assertRunParserRaises(image, data, parser, MetadataValueExistsException)

    # Field not found
    _testFieldNotFound(parser)

    # Bad field type
    data = {'diagnosis_confirm_type': '1'}
    image = _createImage()
    assertRunParserRaises(image, data, parser, BadFieldTypeException)


def testBenignMalignantFieldParser():
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
        image = _createImage()
        _runParser(image, data, parser)
        assert {} == data
        assert {} == image['meta']['unstructured']
        assert {'benign_malignant': value.lower()} == image['meta']['clinical']
        assert {} == image['privateMeta']

    # Autocorrected value
    data = {'benign_malignant': 'INDETERMINABLE'}
    image = _createImage()
    _runParser(image, data, parser)
    assert {} == data
    assert {} == image['meta']['unstructured']
    assert {'benign_malignant': 'indeterminate'} == image['meta']['clinical']
    assert {} == image['privateMeta']

    # Invalid value
    data = {'benign_malignant': 'ok'}
    image = _createImage()
    assertRunParserRaises(image, data, parser, BadFieldTypeException)

    # Alternative field name
    data = {'BEN_MAL': 'benign'}
    image = _createImage()
    _runParser(image, data, parser)
    assert {} == data
    assert {} == image['meta']['unstructured']
    assert {'benign_malignant': 'benign'} == image['meta']['clinical']
    assert {} == image['privateMeta']

    # Unknown values
    for value in unknownValues:
        data = {'benign_malignant': value}
        image = _createImage()
        _runParser(image, data, parser)
        assert {} == data
        assert {} == image['meta']['unstructured']
        assert {'benign_malignant': None} == image['meta']['clinical']
        assert {} == image['privateMeta']

    # Duplicate field
    data = {'benign_malignant': 'indeterminate', 'ben_mal': 'indeterminate'}
    image = _createImage()
    assertRunParserRaises(image, data, parser, MultipleFieldException)

    # Update null value with new value
    data = {'benign_malignant': 'malignant'}
    image = _createImage()
    image['meta']['clinical']['benign_malignant'] = None
    _runParser(image, data, parser)
    assert {} == data
    assert {} == image['meta']['unstructured']
    assert {'benign_malignant': 'malignant'} == image['meta']['clinical']
    assert {} == image['privateMeta']

    # Update existing value with same value
    data = {'benign_malignant': 'malignant'}
    image = _createImage()
    image['meta']['clinical']['benign_malignant'] = 'malignant'
    _runParser(image, data, parser)
    assert {} == data
    assert {} == image['meta']['unstructured']
    assert {'benign_malignant': 'malignant'} == image['meta']['clinical']
    assert {} == image['privateMeta']

    # Update existing value with null value
    data = {'benign_malignant': None}
    image = _createImage()
    image['meta']['clinical']['benign_malignant'] = 'malignant'
    assertRunParserRaises(image, data, parser, MetadataValueExistsException)

    # Update existing value with new value
    data = {'benign_malignant': 'malignant'}
    image = _createImage()
    image['meta']['clinical']['benign_malignant'] = 'benign'
    assertRunParserRaises(image, data, parser, MetadataValueExistsException)

    # Field not found
    _testFieldNotFound(parser)

    # Bad field type
    data = {'benign_malignant': '1'}
    image = _createImage()
    assertRunParserRaises(image, data, parser, BadFieldTypeException)


def testDiagnosisFieldParser():
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
        image = _createImage()
        _runParser(image, data, parser)
        assert {} == data
        assert {} == image['meta']['unstructured']
        assert {'diagnosis': value.lower()} == image['meta']['clinical']
        assert {} == image['privateMeta']

    # Special case: AIMP
    data = {'diagnosis': 'AIMP'}
    image = _createImage()
    _runParser(image, data, parser)
    assert {} == data
    assert {} == image['meta']['unstructured']
    assert {'diagnosis': 'AIMP'} == image['meta']['clinical']
    assert {} == image['privateMeta']

    # Special case: lentigo NOS
    data = {'diagnosis': 'lentigo NOS'}
    image = _createImage()
    _runParser(image, data, parser)
    assert {} == data
    assert {} == image['meta']['unstructured']
    assert {'diagnosis': 'lentigo NOS'} == image['meta']['clinical']
    assert {} == image['privateMeta']

    # Special case: Cafe-au-lait
    data = {'diagnosis': 'caf\xe9-au-lait macule'}
    image = _createImage()
    _runParser(image, data, parser)
    assert {} == data
    assert {} == image['meta']['unstructured']
    assert {'diagnosis': 'cafe-au-lait macule'} == image['meta']['clinical']
    assert {} == image['privateMeta']

    # Alternative field name
    data = {'path_diagnosis': 'melanoma'}
    image = _createImage()
    _runParser(image, data, parser)
    assert {} == data
    assert {} == image['meta']['unstructured']
    assert {'diagnosis': 'melanoma'} == image['meta']['clinical']
    assert {} == image['privateMeta']

    # Invalid value
    data = {'diagnosis': 'bad'}
    image = _createImage()
    assertRunParserRaises(image, data, parser, BadFieldTypeException)

    # Unknown values
    for value in unknownValues:
        data = {'diagnosis': value}
        image = _createImage()
        _runParser(image, data, parser)
        assert {} == data
        assert {} == image['meta']['unstructured']
        assert {'diagnosis': None} == image['meta']['clinical']
        assert {} == image['privateMeta']

    # Duplicate field
    data = {'diagnosis': 'dermatofibroma', 'path_diagnosis': 'dermatofibroma'}
    image = _createImage()
    assertRunParserRaises(image, data, parser, MultipleFieldException)

    # Update null value with new value
    data = {'diagnosis': 'dermatofibroma'}
    image = _createImage()
    image['meta']['clinical']['diagnosis'] = None
    _runParser(image, data, parser)
    assert {} == data
    assert {} == image['meta']['unstructured']
    assert {'diagnosis': 'dermatofibroma'} == image['meta']['clinical']
    assert {} == image['privateMeta']

    # Update existing value with same value
    data = {'diagnosis': 'dermatofibroma'}
    image = _createImage()
    image['meta']['clinical']['diagnosis'] = 'dermatofibroma'
    _runParser(image, data, parser)
    assert {} == data
    assert {} == image['meta']['unstructured']
    assert {'diagnosis': 'dermatofibroma'} == image['meta']['clinical']
    assert {} == image['privateMeta']

    # Update existing value with null value
    data = {'diagnosis': None}
    image = _createImage()
    image['meta']['clinical']['diagnosis'] = 'dermatofibroma'
    assertRunParserRaises(image, data, parser, MetadataValueExistsException)

    # Update existing value with new value
    data = {'diagnosis': 'melanoma'}
    image = _createImage()
    image['meta']['clinical']['diagnosis'] = 'dermatofibroma'
    assertRunParserRaises(image, data, parser, MetadataValueExistsException)

    # Field not found
    _testFieldNotFound(parser)

    # Bad field type
    data = {'diagnosis': '1'}
    image = _createImage()
    assertRunParserRaises(image, data, parser, BadFieldTypeException)


def testNevusTypeFieldParser():
    parser = NevusTypeFieldParser

    # Valid values with varying case
    for value in [
        'blue',
        'combined',
        'deep penetrating',
        'halo',
        'PERSISTENT/RECURRENT',
        'pigmented spindle cell of reed',
        'plexiform spindle cell',
        'special site',
        'spitz'
    ]:
        data = {'nevus_type': value}
        image = _createImage()
        _runParser(image, data, parser)
        assert {} == data
        assert {} == image['meta']['unstructured']
        assert {'nevus_type': value.lower()} == image['meta']['clinical']
        assert {} == image['privateMeta']

    # Special case: nevus NOS
    data = {'nevus_type': 'nevus NOS'}
    image = _createImage()
    _runParser(image, data, parser)
    assert {} == data
    assert {} == image['meta']['unstructured']
    assert {'nevus_type': 'nevus NOS'} == image['meta']['clinical']
    assert {} == image['privateMeta']

    # Invalid value
    data = {'nevus_type': 'bad'}
    image = _createImage()
    assertRunParserRaises(image, data, parser, BadFieldTypeException)

    # Unknown values
    for value in unknownValues:
        data = {'nevus_type': value}
        image = _createImage()
        _runParser(image, data, parser)
        assert {} == data
        assert {} == image['meta']['unstructured']
        assert {'nevus_type': None} == image['meta']['clinical']
        assert {} == image['privateMeta']

    # Update null value with new value
    data = {'nevus_type': 'spitz'}
    image = _createImage()
    image['meta']['clinical']['nevus_type'] = None
    _runParser(image, data, parser)
    assert {} == data
    assert {} == image['meta']['unstructured']
    assert {'nevus_type': 'spitz'} == image['meta']['clinical']
    assert {} == image['privateMeta']

    # Update existing value with same value
    data = {'nevus_type': 'spitz'}
    image = _createImage()
    image['meta']['clinical']['nevus_type'] = 'spitz'
    _runParser(image, data, parser)
    assert {} == data
    assert {} == image['meta']['unstructured']
    assert {'nevus_type': 'spitz'} == image['meta']['clinical']
    assert {} == image['privateMeta']

    # Update existing value with null value
    data = {'nevus_type': None}
    image = _createImage()
    image['meta']['clinical']['nevus_type'] = 'spitz'
    assertRunParserRaises(image, data, parser, MetadataValueExistsException)

    # Update existing value with new value
    data = {'nevus_type': 'halo'}
    image = _createImage()
    image['meta']['clinical']['nevus_type'] = 'spitz'
    assertRunParserRaises(image, data, parser, MetadataValueExistsException)

    # Field not found
    _testFieldNotFound(parser)

    # Bad field type
    data = {'nevus_type': '1'}
    image = _createImage()
    assertRunParserRaises(image, data, parser, BadFieldTypeException)


def testImageTypeFieldParser():
    parser = ImageTypeFieldParser

    # Valid values with varying case
    for value in [
        'dermoscopic',
        'CLINICAL',
        'Overview'
    ]:
        data = {'image_type': value}
        image = _createImage()
        _runParser(image, data, parser)
        assert {} == data
        assert {} == image['meta']['unstructured']
        assert {'image_type': value.lower()} == image['meta']['acquisition']
        assert {} == image['privateMeta']

    # Invalid value
    data = {'image_type': 'bad'}
    image = _createImage()
    assertRunParserRaises(image, data, parser, BadFieldTypeException)

    # Unknown values
    for value in unknownValues:
        data = {'image_type': value}
        image = _createImage()
        _runParser(image, data, parser)
        assert {} == data
        assert {} == image['meta']['unstructured']
        assert {'image_type': None} == image['meta']['acquisition']
        assert {} == image['privateMeta']

    # Update null value with new value
    data = {'image_type': 'dermoscopic'}
    image = _createImage()
    image['meta']['acquisition']['image_type'] = None
    _runParser(image, data, parser)
    assert {} == data
    assert {} == image['meta']['unstructured']
    assert {'image_type': 'dermoscopic'} == image['meta']['acquisition']
    assert {} == image['privateMeta']

    # Update existing value with same value
    data = {'image_type': 'dermoscopic'}
    image = _createImage()
    image['meta']['acquisition']['image_type'] = 'dermoscopic'
    _runParser(image, data, parser)
    assert {} == data
    assert {} == image['meta']['unstructured']
    assert {'image_type': 'dermoscopic'} == image['meta']['acquisition']
    assert {} == image['privateMeta']

    # Update existing value with null value
    data = {'image_type': None}
    image = _createImage()
    image['meta']['acquisition']['image_type'] = 'dermoscopic'
    assertRunParserRaises(image, data, parser, MetadataValueExistsException)

    # Update existing value with new value
    data = {'image_type': 'clinical'}
    image = _createImage()
    image['meta']['acquisition']['image_type'] = 'dermoscopic'
    assertRunParserRaises(image, data, parser, MetadataValueExistsException)

    # Field not found
    _testFieldNotFound(parser)


def testDermoscopicTypeFieldParser():
    parser = DermoscopicTypeFieldParser

    # Valid values with varying case
    for value in [
        'contact polarized',
        'CONTACT NON-POLARIZED',
        'Non-contact Polarized'
    ]:
        data = {'dermoscopic_type': value}
        image = _createImage()
        _runParser(image, data, parser)
        assert {} == data
        assert {} == image['meta']['unstructured']
        assert {'dermoscopic_type': value.lower()} == image['meta']['acquisition']
        assert {} == image['privateMeta']

    # Special case
    data = {'dermoscopic_type': 'contact non polarized'}
    image = _createImage()
    _runParser(image, data, parser)
    assert {} == data
    assert {} == image['meta']['unstructured']
    assert {'dermoscopic_type': 'contact non-polarized'} == image['meta']['acquisition']
    assert {} == image['privateMeta']

    data = {'dermoscopic_type': 'non contact polarized'}
    image = _createImage()
    _runParser(image, data, parser)
    assert {} == data
    assert {} == image['meta']['unstructured']
    assert {'dermoscopic_type': 'non-contact polarized'} == image['meta']['acquisition']
    assert {} == image['privateMeta']

    # Invalid value
    data = {'dermoscopic_type': 'bad'}
    image = _createImage()
    assertRunParserRaises(image, data, parser, BadFieldTypeException)

    # Unknown values
    for value in unknownValues:
        data = {'dermoscopic_type': value}
        image = _createImage()
        _runParser(image, data, parser)
        assert {} == data
        assert {} == image['meta']['unstructured']
        assert {'dermoscopic_type': None} == image['meta']['acquisition']
        assert {} == image['privateMeta']

    # Update null value with new value
    data = {'dermoscopic_type': 'contact polarized'}
    image = _createImage()
    image['meta']['acquisition']['dermoscopic_type'] = None
    _runParser(image, data, parser)
    assert {} == data
    assert {} == image['meta']['unstructured']
    assert {'dermoscopic_type': 'contact polarized'} == image['meta']['acquisition']
    assert {} == image['privateMeta']

    # Update existing value with same value
    data = {'dermoscopic_type': 'contact polarized'}
    image = _createImage()
    image['meta']['acquisition']['dermoscopic_type'] = 'contact polarized'
    _runParser(image, data, parser)
    assert {} == data
    assert {} == image['meta']['unstructured']
    assert {'dermoscopic_type': 'contact polarized'} == image['meta']['acquisition']
    assert {} == image['privateMeta']

    # Update existing value with null value
    data = {'dermoscopic_type': None}
    image = _createImage()
    image['meta']['acquisition']['dermoscopic_type'] = 'contact polarized'
    assertRunParserRaises(image, data, parser, MetadataValueExistsException)

    # Update existing value with new value
    data = {'dermoscopic_type': 'contact non-polarized'}
    image = _createImage()
    image['meta']['acquisition']['dermoscopic_type'] = 'contact polarized'
    assertRunParserRaises(image, data, parser, MetadataValueExistsException)

    # Field not found
    _testFieldNotFound(parser)


def testMelThickMmFieldParser():
    parser = MelThickMmFieldParser

    # Normal
    for value in ['1.23 mm', '1.23mm', '1.23']:
        data = {'mel_thick_mm': value}
        image = _createImage()
        _runParser(image, data, parser)
        assert {} == data
        assert {} == image['meta']['unstructured']
        assert {'mel_thick_mm': 1.23} == image['meta']['clinical']
        assert {} == image['privateMeta']

    # Alternative field name
    data = {'mel_thick': '1.25 mm'}
    image = _createImage()
    _runParser(image, data, parser)
    assert {} == data
    assert {} == image['meta']['unstructured']
    assert {'mel_thick_mm': 1.25} == image['meta']['clinical']
    assert {} == image['privateMeta']

    # Unknown values
    for value in unknownValues:
        data = {'mel_thick_mm': value}
        image = _createImage()
        _runParser(image, data, parser)
        assert {} == data
        assert {} == image['meta']['unstructured']
        assert {'mel_thick_mm': None} == image['meta']['clinical']
        assert {} == image['privateMeta']

    # Update null value with new value
    data = {'mel_thick_mm': '1.23 mm'}
    image = _createImage()
    image['meta']['clinical']['mel_thick_mm'] = None
    _runParser(image, data, parser)
    assert {} == data
    assert {} == image['meta']['unstructured']
    assert {'mel_thick_mm': 1.23} == image['meta']['clinical']
    assert {} == image['privateMeta']

    # Update existing value with same value
    data = {'mel_thick_mm': '1.23 mm'}
    image = _createImage()
    image['meta']['clinical']['mel_thick_mm'] = 1.23
    _runParser(image, data, parser)
    assert {} == data
    assert {} == image['meta']['unstructured']
    assert {'mel_thick_mm': 1.23} == image['meta']['clinical']
    assert {} == image['privateMeta']

    # Update existing value with null value
    data = {'mel_thick_mm': None}
    image = _createImage()
    image['meta']['clinical']['mel_thick_mm'] = 1.23
    assertRunParserRaises(image, data, parser, MetadataValueExistsException)

    # Update existing value with new value
    data = {'mel_thick_mm': '1.23 mm'}
    image = _createImage()
    image['meta']['clinical']['mel_thick_mm'] = 2.1
    assertRunParserRaises(image, data, parser, MetadataValueExistsException)

    # Field not found
    _testFieldNotFound(parser)

    # Bad field type
    data = {'mel_thick_mm': 'true'}
    image = _createImage()
    assertRunParserRaises(image, data, parser, BadFieldTypeException)

    data = {'mel_thick_mm': '1.23 cm'}
    image = _createImage()
    assertRunParserRaises(image, data, parser, BadFieldTypeException)


def testMelClassFieldParser():
    parser = MelClassFieldParser

    # Valid values with varying case
    for value in [
        'melanoma in situ',
        'invasive melanoma',
        'recurrent/persistent melanoma, in situ',
        'RECURRENT/PERSISTENT MELANOMA, INVASIVE',
    ]:
        data = {'mel_class': value}
        image = _createImage()
        _runParser(image, data, parser)
        assert {} == data
        assert {} == image['meta']['unstructured']
        assert {'mel_class': value.lower()} == image['meta']['clinical']
        assert {} == image['privateMeta']

    # Special case
    data = {'mel_class': 'recurrent/persistent melanoma in situ'}
    image = _createImage()
    _runParser(image, data, parser)
    assert {} == data
    assert {} == image['meta']['unstructured']
    assert {'mel_class': 'recurrent/persistent melanoma, in situ'} == image['meta']['clinical']
    assert {} == image['privateMeta']

    # Special case
    data = {'mel_class': 'recurrent/persistent melanoma invasive'}
    image = _createImage()
    _runParser(image, data, parser)
    assert {} == data
    assert {} == image['meta']['unstructured']
    assert {'mel_class': 'recurrent/persistent melanoma, invasive'} == image['meta']['clinical']
    assert {} == image['privateMeta']

    # Special case
    data = {'mel_class': 'melanoma nos'}
    image = _createImage()
    _runParser(image, data, parser)
    assert {} == data
    assert {} == image['meta']['unstructured']
    assert {'mel_class': 'melanoma NOS'} == image['meta']['clinical']
    assert {} == image['privateMeta']

    # Invalid value
    data = {'mel_class': 'bad'}
    image = _createImage()
    assertRunParserRaises(image, data, parser, BadFieldTypeException)

    # Unknown values
    for value in unknownValues:
        data = {'mel_class': value}
        image = _createImage()
        _runParser(image, data, parser)
        assert {} == data
        assert {} == image['meta']['unstructured']
        assert {'mel_class': None} == image['meta']['clinical']
        assert {} == image['privateMeta']

    # Update null value with new value
    data = {'mel_class': 'melanoma in situ'}
    image = _createImage()
    image['meta']['clinical']['mel_class'] = None
    _runParser(image, data, parser)
    assert {} == data
    assert {} == image['meta']['unstructured']
    assert {'mel_class': 'melanoma in situ'} == image['meta']['clinical']
    assert {} == image['privateMeta']

    # Update existing value with same value
    data = {'mel_class': 'melanoma in situ'}
    image = _createImage()
    image['meta']['clinical']['mel_class'] = 'melanoma in situ'
    _runParser(image, data, parser)
    assert {} == data
    assert {} == image['meta']['unstructured']
    assert {'mel_class': 'melanoma in situ'} == image['meta']['clinical']
    assert {} == image['privateMeta']

    # Update existing value with null value
    data = {'mel_class': None}
    image = _createImage()
    image['meta']['clinical']['mel_class'] = 'melanoma in situ'
    assertRunParserRaises(image, data, parser, MetadataValueExistsException)

    # Update existing value with new value
    data = {'mel_class': 'melanoma nos'}
    image = _createImage()
    image['meta']['clinical']['mel_class'] = 'melanoma in situ'
    assertRunParserRaises(image, data, parser, MetadataValueExistsException)

    # Field not found
    _testFieldNotFound(parser)


def testMelTypeFieldParser():
    parser = MelTypeFieldParser

    # Valid values with varying case
    for value in [
        'superficial spreading melanoma',
        'nodular melanoma',
        'lentigo maligna melanoma',
        'ACRAL LENTIGINOUS MELANOMA'
    ]:
        data = {'mel_type': value}
        image = _createImage()
        _runParser(image, data, parser)
        assert {} == data
        assert {} == image['meta']['unstructured']
        assert {'mel_type': value.lower()} == image['meta']['clinical']
        assert {} == image['privateMeta']

    # Special case
    data = {'mel_type': 'ssm'}
    image = _createImage()
    _runParser(image, data, parser)
    assert {} == data
    assert {} == image['meta']['unstructured']
    assert {'mel_type': 'superficial spreading melanoma'} == image['meta']['clinical']
    assert {} == image['privateMeta']

    # Special case
    data = {'mel_type': 'lmm'}
    image = _createImage()
    _runParser(image, data, parser)
    assert {} == data
    assert {} == image['meta']['unstructured']
    assert {'mel_type': 'lentigo maligna melanoma'} == image['meta']['clinical']
    assert {} == image['privateMeta']

    # Special case
    data = {'mel_type': 'alm'}
    image = _createImage()
    _runParser(image, data, parser)
    assert {} == data
    assert {} == image['meta']['unstructured']
    assert {'mel_type': 'acral lentiginous melanoma'} == image['meta']['clinical']
    assert {} == image['privateMeta']

    # Special case
    data = {'mel_type': 'melanoma nos'}
    image = _createImage()
    _runParser(image, data, parser)
    assert {} == data
    assert {} == image['meta']['unstructured']
    assert {'mel_type': 'melanoma NOS'} == image['meta']['clinical']
    assert {} == image['privateMeta']

    # Invalid value
    data = {'mel_type': 'bad'}
    image = _createImage()
    assertRunParserRaises(image, data, parser, BadFieldTypeException)

    # Unknown values
    for value in unknownValues:
        data = {'mel_type': value}
        image = _createImage()
        _runParser(image, data, parser)
        assert {} == data
        assert {} == image['meta']['unstructured']
        assert {'mel_type': None} == image['meta']['clinical']
        assert {} == image['privateMeta']

    # Update null value with new value
    data = {'mel_type': 'nodular melanoma'}
    image = _createImage()
    image['meta']['clinical']['mel_type'] = None
    _runParser(image, data, parser)
    assert {} == data
    assert {} == image['meta']['unstructured']
    assert {'mel_type': 'nodular melanoma'} == image['meta']['clinical']
    assert {} == image['privateMeta']

    # Update existing value with same value
    data = {'mel_type': 'nodular melanoma'}
    image = _createImage()
    image['meta']['clinical']['mel_type'] = 'nodular melanoma'
    _runParser(image, data, parser)
    assert {} == data
    assert {} == image['meta']['unstructured']
    assert {'mel_type': 'nodular melanoma'} == image['meta']['clinical']
    assert {} == image['privateMeta']

    # Update existing value with null value
    data = {'mel_type': None}
    image = _createImage()
    image['meta']['clinical']['mel_type'] = 'nodular melanoma'
    assertRunParserRaises(image, data, parser, MetadataValueExistsException)

    # Update existing value with new value
    data = {'mel_type': 'acral lentiginous melanoma'}
    image = _createImage()
    image['meta']['clinical']['mel_type'] = 'nodular melanoma'
    assertRunParserRaises(image, data, parser, MetadataValueExistsException)

    # Field not found
    _testFieldNotFound(parser)


def testMelMitoticIndexFieldParser():
    parser = MelMitoticIndexFieldParser

    # Valid values with varying case
    for value in [
        '0/mm^2',
        '<1/mm^2',
        '1/mm^2',
        '2/mm^2',
        '3/mm^2',
        '4/MM^2',
        '>4/mm^2'
    ]:
        data = {'mel_mitotic_index': value}
        image = _createImage()
        _runParser(image, data, parser)
        assert {} == data
        assert {} == image['meta']['unstructured']
        assert {'mel_mitotic_index': value.lower()} == image['meta']['clinical']
        assert {} == image['privateMeta']

    # Valid value with non-standard units
    data = {'mel_mitotic_index': '2/mm2'}
    image = _createImage()
    _runParser(image, data, parser)
    assert {'mel_mitotic_index': '2/mm^2'} == image['meta']['clinical']

    # Invalid value
    data = {'mel_mitotic_index': 'bad'}
    image = _createImage()
    assertRunParserRaises(image, data, parser, BadFieldTypeException)

    # Unknown values
    for value in unknownValues:
        data = {'mel_mitotic_index': value}
        image = _createImage()
        _runParser(image, data, parser)
        assert {} == data
        assert {} == image['meta']['unstructured']
        assert {'mel_mitotic_index': None} == image['meta']['clinical']
        assert {} == image['privateMeta']

    # Update null value with new value
    data = {'mel_mitotic_index': '1/mm^2'}
    image = _createImage()
    image['meta']['clinical']['mel_mitotic_index'] = None
    _runParser(image, data, parser)
    assert {} == data
    assert {} == image['meta']['unstructured']
    assert {'mel_mitotic_index': '1/mm^2'} == image['meta']['clinical']
    assert {} == image['privateMeta']

    # Update existing value with same value
    data = {'mel_mitotic_index': '1/mm^2'}
    image = _createImage()
    image['meta']['clinical']['mel_mitotic_index'] = '1/mm^2'
    _runParser(image, data, parser)
    assert {} == data
    assert {} == image['meta']['unstructured']
    assert {'mel_mitotic_index': '1/mm^2'} == image['meta']['clinical']
    assert {} == image['privateMeta']

    # Update existing value with null value
    data = {'mel_mitotic_index': None}
    image = _createImage()
    image['meta']['clinical']['mel_mitotic_index'] = '1/mm^2'
    assertRunParserRaises(image, data, parser, MetadataValueExistsException)

    # Update existing value with new value
    data = {'mel_mitotic_index': '<1/mm^2'}
    image = _createImage()
    image['meta']['clinical']['mel_mitotic_index'] = '1/mm^2'
    assertRunParserRaises(image, data, parser, MetadataValueExistsException)

    # Field not found
    _testFieldNotFound(parser)


def testMelUlcerFieldParser():
    parser = MelUlcerFieldParser

    # Normal
    data = {'mel_ulcer': 'false'}
    image = _createImage()
    _runParser(image, data, parser)
    assert {} == data
    assert {} == image['meta']['unstructured']
    assert {'mel_ulcer': False} == image['meta']['clinical']
    assert {} == image['privateMeta']

    # Unknown values
    for value in unknownValues:
        data = {'mel_ulcer': value}
        image = _createImage()
        _runParser(image, data, parser)
        assert {} == data
        assert {} == image['meta']['unstructured']
        assert {'mel_ulcer': None} == image['meta']['clinical']
        assert {} == image['privateMeta']

    # Update null value with new value
    data = {'mel_ulcer': 'true'}
    image = _createImage()
    image['meta']['clinical']['mel_ulcer'] = None
    _runParser(image, data, parser)
    assert {} == data
    assert {} == image['meta']['unstructured']
    assert {'mel_ulcer': True} == image['meta']['clinical']
    assert {} == image['privateMeta']

    # Update existing value with same value
    data = {'mel_ulcer': 'true'}
    image = _createImage()
    image['meta']['clinical']['mel_ulcer'] = True
    _runParser(image, data, parser)
    assert {} == data
    assert {} == image['meta']['unstructured']
    assert {'mel_ulcer': True} == image['meta']['clinical']
    assert {} == image['privateMeta']

    # Update existing value with null value
    data = {'mel_ulcer': None}
    image = _createImage()
    image['meta']['clinical']['mel_ulcer'] = True
    assertRunParserRaises(image, data, parser, MetadataValueExistsException)

    # Update existing value with new value
    data = {'mel_ulcer': 'true'}
    image = _createImage()
    image['meta']['clinical']['mel_ulcer'] = False
    assertRunParserRaises(image, data, parser, MetadataValueExistsException)

    # Field not found
    _testFieldNotFound(parser)

    # Bad field type
    data = {'mel_ulcer': '1'}
    image = _createImage()


def testGeneralAnatomicSiteFieldParser():
    parser = GeneralAnatomicSiteFieldParser

    data = {'anatom_site_general': 'head/neck'}
    image = _createImage()
    _runParser(image, data, parser)
    assert {'anatom_site_general': 'head/neck'} == image['meta']['clinical']


def testPatientIdFieldParser():
    parser = PatientIdFieldParser

    data = {'patient_id': 'ip_0123456 '}
    image = _createImage()
    _runParser(image, data, parser)
    assert {'patient_id': 'IP_0123456'} == image['meta']['clinical']


def testLesionIdFieldParser():
    parser = LesionIdFieldParser

    data = {'lesion_id': 'il_0123456 '}
    image = _createImage()
    _runParser(image, data, parser)
    assert {'lesion_id': 'IL_0123456'} == image['meta']['clinical']


def testAddImageClinicalMetadata():
    # Empty data
    data = {}
    image = _createImage()
    errors, unrecognizedFields = addImageMetadata(image, data)
    assert [] == errors
    assert 0 == len(unrecognizedFields)

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
        'anatom_site_general': 'head/neck',
        'anatomic': 'neck'
    }
    image = _createImage()
    image['meta']['clinical']['sex'] = 'female'
    image['meta']['unstructured']['laterality'] = 'left'
    errors, warnings = addImageMetadata(image, data)
    assert [] == errors
    assert {
        'anatomic': 'neck',
        'laterality': 'left'
    } == image['meta']['unstructured']
    assert {
        'age_approx': 45,
        'anatom_site_general': 'head/neck',
        'sex': 'female',
        'family_hx_mm': False,
        'personal_hx_mm': False,
        'clin_size_long_diam_mm': 3.0,
        'melanocytic': True,
        'diagnosis_confirm_type': 'histopathology',
        'benign_malignant': 'malignant',
        'diagnosis': 'melanoma',
    } == image['meta']['clinical']
    assert {
        'age': 45
    } == image['privateMeta']
    assert 1 == len(warnings)
    assert "unrecognized field 'anatomic' will be added to unstructured metadata" in \
        warnings

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
    image = _createImage()
    image['meta']['clinical']['sex'] = 'male'
    image['meta']['clinical']['melanocytic'] = False
    errors, warnings = addImageMetadata(image, data)
    assert 5 == len(errors)
    assert "value already exists for field 'sex' (old: 'male', new: 'female')" in \
        errors
    assert "value is wrong type for field 'clin_size_long_diam_mm' " \
        "(expected 'float with units (um, mm, or cm)', value: '3.0+')" in \
        errors
    assert "value already exists for field 'melanocytic' (old: False, new: None)" in \
        errors
    assert "only one of field 'benign_malignant' may be present, " \
        "found: ['ben_mal', 'benign_malignant']" in \
        errors
    assert 1 == len(warnings)
    assert "corrected inconsistent value for field 'melanocytic' based on field 'diagnosis' " \
        "(new value: True, 'diagnosis': 'melanoma')" in \
        warnings


def testAddImageClinicalMetadataInterfieldValidation():
    # Valid cases
    data = {
        'benign_malignant': None,
        'diagnosis': 'melanoma',
        'diagnosis_confirm_type': 'histopathology'
    }
    image = _createImage()
    errors, _ = addImageMetadata(image, data)
    assert [] == errors
    assert 'malignant' == image['meta']['clinical']['benign_malignant']

    data = {
        'benign_malignant': None,
        'diagnosis': 'nevus',
        'diagnosis_confirm_type': 'single image expert consensus'
    }
    image = _createImage()
    errors, _ = addImageMetadata(image, data)
    assert [] == errors
    assert 'benign' == image['meta']['clinical']['benign_malignant']

    data = {
        'benign_malignant': 'indeterminate',
        'diagnosis': 'other',
        'diagnosis_confirm_type': 'histopathology'
    }
    image = _createImage()
    errors, _ = addImageMetadata(image, data)
    assert [] == errors

    data = {
        'mel_thick_mm': '1.23 mm',
        'diagnosis': 'melanoma',
        'diagnosis_confirm_type': 'histopathology'
    }
    image = _createImage()
    errors, _ = addImageMetadata(image, data)
    assert [] == errors

    data = {
        'nevus_type': 'blue',
        'diagnosis': 'nevus',
        'benign_malignant': 'benign'
    }
    image = _createImage()
    errors, _ = addImageMetadata(image, data)
    assert [] == errors

    data = {
        'image_type': 'dermoscopic',
        'dermoscopic_type': 'contact polarized'
    }
    image = _createImage()
    errors, _ = addImageMetadata(image, data)
    assert [] == errors

    data = {
        'image_type': 'clinical',
        'dermoscopic_type': None
    }
    image = _createImage()
    errors, _ = addImageMetadata(image, data)
    assert [] == errors

    data = {
        'image_type': None,
        'dermoscopic_type': 'contact non-polarized'
    }
    image = _createImage()
    errors, _ = addImageMetadata(image, data)
    assert [] == errors
    assert 'dermoscopic' == image['meta']['acquisition']['image_type']

    # Error cases
    data = {
        'benign_malignant': 'benign',
        'diagnosis': 'melanoma',
    }
    image = _createImage()
    errors, _ = addImageMetadata(image, data)
    assert 1 == len(errors)

    data = {
        'benign_malignant': 'malignant',
        'diagnosis': 'nevus',
    }
    image = _createImage()
    errors, _ = addImageMetadata(image, data)
    assert 1 == len(errors)

    data = {
        'benign_malignant': 'indeterminate',
        'diagnosis': 'other',
        'diagnosis_confirm_type': 'single image expert consensus'
    }
    image = _createImage()
    errors, _ = addImageMetadata(image, data)
    assert 1 == len(errors)

    data = {
        'mel_thick_mm': '1.23 mm',
        'diagnosis': 'other'
    }
    image = _createImage()
    errors, _ = addImageMetadata(image, data)
    assert 1 == len(errors)

    data = {
        'nevus_type': 'blue',
        'diagnosis': 'other'
    }
    image = _createImage()
    errors, _ = addImageMetadata(image, data)
    assert 1 == len(errors)

    data = {
        'image_type': 'clinical',
        'dermoscopic_type': 'contact polarized'
    }
    image = _createImage()
    errors, _ = addImageMetadata(image, data)
    assert 1 == len(errors)

    # Warning cases
    data = {
        'benign_malignant': 'benign',
        'diagnosis': 'basal cell carcinoma',
    }
    image = _createImage()
    errors, warnings = addImageMetadata(image, data)
    assert [] == errors
    assert 1 == len(warnings)


def testAddImageMetadataExif():
    data = {
        'exif_1': 'value1',
        'exif_2': 'value2',
        'EXIF_3': 'value3'
    }
    image = _createImage()
    errors, _ = addImageMetadata(image, data)
    assert [] == errors
    assert 'value1' == image['meta']['unstructuredExif']['exif_1']
    assert 'value2' == image['meta']['unstructuredExif']['exif_2']
    assert 'value3' == image['meta']['unstructuredExif']['EXIF_3']


def testMelanocyticValidation():
    # Test populating melanocytic field based on diagnosis
    data = {
        'benign_malignant': 'malignant',
        'diagnosis': 'melanoma',
        'diagnosis_confirm_type': 'histopathology',
        'melanocytic': None
    }
    image = _createImage()
    errors, warnings = addImageMetadata(image, data)
    assert [] == errors
    assert [] == warnings
    assert image['meta']['clinical']['melanocytic']

    # Test autocorrecting inconsistent melanocytic field to True based on diagnosis
    data = {
        'benign_malignant': 'malignant',
        'diagnosis': 'melanoma',
        'diagnosis_confirm_type': 'histopathology',
        'melanocytic': False
    }
    image = _createImage()
    errors, warnings = addImageMetadata(image, data)
    assert [] == errors
    assert 1 == len(warnings)
    assert image['meta']['clinical']['melanocytic']

    # Test autocorrecting inconsistent melanocytic field to False based on diagnosis
    data = {
        'diagnosis': 'verruca',
        'melanocytic': True
    }
    image = _createImage()
    errors, warnings = addImageMetadata(image, data)
    assert [] == errors
    assert 1 == len(warnings)
    assert not image['meta']['clinical']['melanocytic']
