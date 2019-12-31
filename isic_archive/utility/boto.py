from typing import Dict

from boto3.session import Session

from isic_archive import settings

s3Kwargs: Dict[str, str] = {}

if settings.ISIC_UPLOAD_S3_URL:
    s3Kwargs = {
        'endpoint_url': settings.ISIC_UPLOAD_S3_URL,
        'aws_access_key_id': 'accesskey',
        'aws_secret_access_key': 'secretkey'
    }

session = Session()
s3 = session.client('s3', **s3Kwargs)
sts = session.client('sts')

if settings.ISIC_UPLOAD_S3_URL:
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
