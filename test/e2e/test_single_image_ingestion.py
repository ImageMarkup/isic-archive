import time
from time import sleep

import pytest

from isic_archive.models.image import Image


@pytest.mark.parametrize(
    'filename,readable',
    [['should-pass.jpg', True], ['should-skip', False]],
    ids=['readable-image', 'unreadable-text-file'],
)
def test_single_image_ingestion(session, dataset_id, filename, readable):
    with open(f'test/data/{filename}', 'rb') as infile:
        r = session.post(
            'dataset/%s/image' % dataset_id,
            params={'signature': 'test', 'filename': filename},
            data=infile.read(),
        )
        r.raise_for_status()

    image = Image().load(r.json()['_id'], force=True)
    start = time.time()
    while not image['ingested']:
        image = Image().load(r.json()['_id'], force=True)
        if time.time() - start > 120:
            assert False, 'timed out'
        sleep(10)

    assert image['readable'] == readable
