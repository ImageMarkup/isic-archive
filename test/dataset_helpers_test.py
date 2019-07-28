import re

from isic_archive.models.dataset_helpers import matchFilenameRegex


def assertMatch(originalFilename, csvFilename):
    """Assert that the filename in the CSV matches the original filename."""
    regex = matchFilenameRegex(csvFilename)
    assert re.match(regex, originalFilename) is not None


def assertNotMatch(originalFilename, csvFilename):
    """Assert that the filename in the CSV doesn't match the original filename."""
    regex = matchFilenameRegex(csvFilename)
    assert re.match(regex, originalFilename) is None


def testMatchFilenameRegex():
    """
    Test matchFilenameRegex.

    The matchFilenameRegex function generates a regular expression to match image
    filenames in a metadata CSV file to original image filenames in the database.
    """
    originalFilename = 'ABC-6D.JPG'
    assertMatch(originalFilename, 'ABC-6D')
    assertMatch(originalFilename, 'ABC-6D.JPG')
    assertMatch(originalFilename, 'ABC-6D.jpg')
    assertMatch(originalFilename, 'abc-6D.jpg')
    assertMatch(originalFilename, 'abc-6d.jpg')
    assertNotMatch(originalFilename, 'ABC-6D.png')
    assertNotMatch(originalFilename, 'ABC-6D.PNG')

    originalFilename = '20010425124238356.jpg'
    assertMatch(originalFilename, '20010425124238356')
    assertMatch(originalFilename, '20010425124238356.jpg')
    assertMatch(originalFilename, '20010425124238356.JPG')
    assertNotMatch(originalFilename, '20010425124238356.png')
    assertNotMatch(originalFilename, '20010425124238356.PNG')

    originalFilename = 'AbcDef00598.jpg'
    assertMatch(originalFilename, 'AbcDef00598')
    assertMatch(originalFilename, 'AbcDef00598.jpg')
    assertMatch(originalFilename, 'AbcDef00598.JPG')
    assertMatch(originalFilename, 'abcdef00598.JPG')
    assertNotMatch(originalFilename, 'AbcDef00598.png')
    assertNotMatch(originalFilename, 'AbcDef00598.PNG')

    originalFilename = 'test-20010425124238356.jpg'
    assertMatch(originalFilename, 'test-20010425124238356')
    assertMatch(originalFilename, 'test-20010425124238356.jpg')
    assertMatch(originalFilename, 'TEST-20010425124238356.jpg')
    assertMatch(originalFilename, 'TEST-20010425124238356.JPG')
    assertNotMatch(originalFilename, 'TEST-20010425124238356.png')
    assertNotMatch(originalFilename, 'TEST-20010425124238356.PNG')

    originalFilename = 'AEOU3014, (20020901020318037) 20010425124238356.jpg'
    assertMatch(originalFilename, 'AEOU3014, (20020901020318037) 20010425124238356')
    assertMatch(originalFilename, 'AEOU3014, (20020901020318037) 20010425124238356.jpg')
    assertMatch(originalFilename, 'AEOU3014, (20020901020318037) 20010425124238356.JPG')
    assertMatch(originalFilename, 'aeou3014, (20020901020318037) 20010425124238356.JPG')
    assertMatch(originalFilename, 'aeou3014, (20020901020318037) 20010425124238356.jpg')
    assertNotMatch(originalFilename, 'AEOU3014, (20020901020318037) 20010425124238356.png')
    assertNotMatch(originalFilename, 'AEOU3014, (20020901020318037) 20010425124238356.PNG')

    originalFilename = '20020901020318037_30445187_2002-0901_Null_ 001.jpg'
    assertMatch(originalFilename, '20020901020318037_30445187_2002-0901_Null_ 001')
    assertMatch(originalFilename, '20020901020318037_30445187_2002-0901_Null_ 001.jpg')
    assertMatch(originalFilename, '20020901020318037_30445187_2002-0901_Null_ 001.JPG')
    assertMatch(originalFilename, '20020901020318037_30445187_2002-0901_NULL_ 001.jpg')
    assertMatch(originalFilename, '20020901020318037_30445187_2002-0901_NULL_ 001.JPG')
    assertNotMatch(originalFilename, '20020901020318037_30445187_2002-0901_NULL_ 001.png')
    assertNotMatch(originalFilename, '20020901020318037_30445187_2002-0901_NULL_ 001.PNG')

    # Filename that contains a period
    originalFilename = 'test.315704d.jpg'
    assertMatch(originalFilename, 'test.315704d')
    assertMatch(originalFilename, 'test.315704d.jpg')
    assertNotMatch(originalFilename, 'test.315704d.PNG')

    # Filename that contains multiple periods
    originalFilename = 'test.315704d.4e95e3d.png'
    assertMatch(originalFilename, 'test.315704d.4e95e3d')
    assertMatch(originalFilename, 'test.315704d.4e95e3d.png')
    assertNotMatch(originalFilename, 'test.315704d')
    assertNotMatch(originalFilename, 'test.315704d.4e95e3d.')
    assertNotMatch(originalFilename, 'test.315704d.4e95e3d.jpg')
