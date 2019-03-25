import time

import boto3

from requests_toolbelt.sessions import BaseUrlSession

@pytest.mark.parametrize('zip_filename, item_names', [
    ['isic-images-uda2-female-wreadme.zip', [

    ]
])
def test_zip_ingestion():
    s = BaseUrlSession('http://localhost:8080/api/v1/')

    r = s.get('user/authentication', auth=('admin',
                                           'password'))
    r.raise_for_status()

    s.headers.update({'Girder-Token': r.json()['authToken']['token']})

    r = s.get('dataset', params={'limit': 1})
    r.raise_for_status()

    if r.json():
        dataset_id = r.json()[0]['_id']
    else:
        r = s.post('dataset', data={
            'name': 'test dataset',
            'description': 'test dataset',
            'license': 'CC-BY',
            'attribution': 'test',
            'owner': 'test'
        })
        r.raise_for_status()
        dataset_id = r.json()['_id']

    # delete items in folder

    r = s.post('dataset/%s/zip' % dataset_id, data={'signature': 'test'})
    r.raise_for_status()

    s3 = boto3.client(
        's3',
        aws_access_key_id=r.json()['accessKeyId'],
        aws_secret_access_key=r.json()['secretAccessKey'],
        endpoint_url='http://localhost:9000',
    )

    with open('isic-images-uda2-female-wreadme.zip', 'rb') as data:
        s3.upload_fileobj(Fileobj=data, Bucket=r.json()['bucketName'], Key=r.json()['objectKey'])

    batch_id = r.json()['batchId']

    r = s.post('dataset/%s/zip/%s' % (dataset_id, batch_id))
    r.raise_for_status()

    start = time.time()
    while True:
        if time.time() - start > 120:
            assert False, 'timed out'

        sleep(10)
