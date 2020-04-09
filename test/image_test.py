import re

from isic_archive.models import Image


def testIsicIdGeneration(provisionedServer):
    randomId = Image.generateIsicId()
    assert re.match(r'^ISIC_\d{7}$', randomId)
