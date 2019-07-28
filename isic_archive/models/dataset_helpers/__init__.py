import os
import re


def matchFilenameRegex(filename):
    """
    Generate a regex to match image filenames in a metadata CSV file to original image filenames.

    The filenames in the CSV may or may not include file extensions. When the
    filename does include an extension, it must match the extension of the
    original filename. The extension must be in the list of valid extensions.

    The comparison ignores case.

    :param filename: The image filename in the CSV file.
    :return: The regular expression.
    """
    # Split filename into root and extension.
    # If the extension is not empty, it begins with a period.
    root, extension = os.path.splitext(filename)

    # If the detected extension isn't recognized, assume it's part of the
    # filename. This allows filenames to contain periods.
    validExtensions = [
        'bmp',
        'jpeg',
        'jpg',
        'png',
        'tif',
        'tiff',
    ]
    if extension and extension.lower()[1:] not in validExtensions:
        root += extension
        extension = ''

    # Escape special characters in filename components
    root = re.escape(root)
    extension = re.escape(extension)

    # When no extension is provided, match any extension
    if not extension:
        extension = r'\.\w+'

    # Compile regular expression
    pattern = f'^{root}{extension}$'
    regex = re.compile(pattern, re.IGNORECASE)

    return regex
