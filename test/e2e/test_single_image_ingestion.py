import time
from time import sleep

import pytest

from isic_archive.models.image import Image


@pytest.mark.parametrize(
    'filename,readable',
    [
        ['should-pass.jpg', True],
        ['should-skip', False],
        ['should-pass-has-exif-orientation.jpg', True],
    ],
    ids=['readable-image', 'unreadable-text-file', 'should-pass-has-exif-orientation'],
)
def test_single_image_ingestion(session, dataset_id, filename, readable):
    with open(f'test/data/{filename}', 'rb') as infile:
        r = session.post(
            f'dataset/{dataset_id}/image',
            params={'signature': 'test', 'filename': filename},
            data=infile.read(),
        )
        r.raise_for_status()

    image = Image().load(r.json()['_id'], force=True)
    start = time.time()
    while not image['ingested']:
        image = Image().load(r.json()['_id'], force=True)
        if time.time() - start > 120:
            raise AssertionError('timed out')
        sleep(10)

    assert image['readable'] == readable

    if readable:
        r = session.get(f'item/{image["_id"]}/tiles')
        assert r.ok, r.json()
