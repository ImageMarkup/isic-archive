from typing import Dict

from boto3.session import Session

from girder.utility.config import getConfig

developmentMode = getConfig()['server']['mode'] == 'development'

s3Kwargs: Dict[str, str] = {}

if developmentMode:
    s3Kwargs = {
        'endpoint_url': 'http://minio:9000',
        'aws_access_key_id': 'accesskey',
        'aws_secret_access_key': 'secretkey'
    }

session = Session()
s3 = session.client('s3', **s3Kwargs)
sts = session.client('sts')

if developmentMode:
    def mockStsAssumeRole(*args, **kwargs):
        return {
            'Credentials':
                {
                    'AccessKeyId': 'accesskey',
                    'SecretAccessKey': 'secretkey',
                    'SessionToken': 'baz'
                }
        }

    sts.assume_role = mockStsAssumeRole
