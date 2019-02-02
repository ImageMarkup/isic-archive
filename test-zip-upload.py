import boto3

from requests_toolbelt.sessions import BaseUrlSession


s = BaseUrlSession('http://isic-archive.test/api/v1/')

r = s.get('user/authentication', auth=('admin', 'password'))
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


r = s.post('dataset/%s/zip' % dataset_id, data={'signature': 'test'})
r.raise_for_status()

s3 = boto3.client(
    's3',
    aws_access_key_id=r.json()['accessKeyId'],
    aws_secret_access_key=r.json()['secretAccessKey'],
    endpoint_url='http://isic-archive.test:4572',
)

with open('isic-images-uda2-female-wreadme.zip', 'rb') as data:
    s3.upload_fileobj(Fileobj=data, Bucket='test-upload-bucket', Key=r.json()['objectKey'])

# Store batch identifier
batch_id = r.json()['batchId']

r = s.post('dataset/%s/zip/%s' % (dataset_id, batch_id))
r.raise_for_status()

# celery deployment
# vagrant testing
