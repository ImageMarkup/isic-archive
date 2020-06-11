import os
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv


_dotenvPath = Path.home() / '.girder' / '.env'
if _dotenvPath.is_file():
    load_dotenv(dotenv_path=_dotenvPath, override=False)

ISIC_ADMIN_PASSWORD: Optional[str] = os.environ.get('ISIC_ADMIN_PASSWORD')
ISIC_API_URL: str = os.environ['ISIC_API_URL'].rstrip('/') + '/'
ISIC_SITE_URL: str = os.environ['ISIC_SITE_URL']
ISIC_ASSETSTORE_PATH: Path = Path(os.environ['ISIC_ASSETSTORE_PATH'])
ISIC_CORS_ORIGINS: List[str] = list(filter(
    None,
    map(
        lambda origin: origin.strip(),
        os.environ.get('ISIC_CORS_ORIGINS', '').split(',')
    )
))
ISIC_UPLOAD_S3_URL: Optional[str] = os.environ.get('ISIC_UPLOAD_S3_URL')
ISIC_UPLOAD_ACCESS_KEY: Optional[str] = os.environ.get('ISIC_UPLOAD_ACCESS_KEY')
ISIC_UPLOAD_SECRET_KEY: Optional[str] = os.environ.get('ISIC_UPLOAD_SECRET_KEY')
if ISIC_UPLOAD_S3_URL:
    assert ISIC_UPLOAD_ACCESS_KEY
    assert ISIC_UPLOAD_SECRET_KEY
ISIC_UPLOAD_BUCKET_NAME: str = os.environ['ISIC_UPLOAD_BUCKET_NAME']
ISIC_UPLOAD_ROLE_ARN: str = os.environ['ISIC_UPLOAD_ROLE_ARN']
# SMTP config
ISIC_SMTP_HOST: Optional[str] = os.environ.get('ISIC_SMTP_HOST')
ISIC_SMTP_PORT: Optional[int] = \
    int(os.environ['ISIC_SMTP_PORT']) if 'ISIC_SMTP_PORT' in os.environ else None
ISIC_SMTP_USERNAME: Optional[str] = os.environ.get('ISIC_SMTP_USERNAME')
ISIC_SMTP_PASSWORD: Optional[str] = os.environ.get('ISIC_SMTP_PASSWORD')
ISIC_SMTP_ENCRYPTION: Optional[str] = os.environ.get('ISIC_SMTP_ENCRYPTION')

# These are picked up automatically by Celery's config
assert os.environ['CELERY_BROKER_URL']
assert os.environ['CELERY_RESULT_BACKEND']

# These are picked up automatically by Sentry's config, and optional
if os.environ.get('SENTRY_DSN'):
    assert os.environ['SENTRY_ENVIRONMENT']
