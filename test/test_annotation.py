import pytest

from isic_archive import IsicArchive

from .fixtures import *  # noqa


@pytest.mark.plugin("isic_archive", IsicArchive)
def test_submit_annotation(dataset, image_ingester):
    image = image_ingester("test/data/should-pass.jpg")
    assert image["readable"]
    assert image["ingested"]
    assert image["ingestionState"] == {"largeImage": True, "superpixelMask": True}
