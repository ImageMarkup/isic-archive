import time
from time import sleep

import boto3

from isic_archive.models.batch import Batch
from isic_archive.models.image import Image


def test_zip_ingestion(session, dataset_id):
    r = session.post('dataset/%s/zip' % dataset_id, data={'signature': 'test'})
    r.raise_for_status()

    s3 = boto3.client(
        's3',
        aws_access_key_id=r.json()['accessKeyId'],
        aws_secret_access_key=r.json()['secretAccessKey'],
        endpoint_url='http://minio:9000',
    )

    with open('test/data/minimal-2-valid-1-skipped.zip', 'rb') as data:
        s3.upload_fileobj(Fileobj=data, Bucket=r.json()['bucketName'], Key=r.json()['objectKey'])

    batch_id = r.json()['batchId']
    batch = Batch().load(batch_id)

    r = session.post('dataset/%s/zip/%s' % (dataset_id, batch_id))
    r.raise_for_status()

    start = time.time()
    while batch['ingestStatus'] != 'notified':
        batch = Batch().load(batch_id)
        if time.time() - start > 120:
            assert False, 'timed out'
        sleep(10)

    assert list(Batch().imagesFailedIngest(batch)) == []
    assert [x['privateMeta']['originalFilename'] for x in Batch().imagesSkippedIngest(batch)] == [
        'should-skip'
    ]
    ingestedFiles = set(
        [
            x['privateMeta']['originalFilename']
            for x in Image().find(
                {
                    'meta.batchId': batch['_id'],
                    '$and': [
                        {'ingestionState.largeImage': True},
                        {'ingestionState.superpixelMask': True},
                    ],
                },
                fields=['privateMeta.originalFilename'],
            )
        ]
    )
    assert ingestedFiles == set(['should-pass.jpg', 'should-pass-2.jpg'])
