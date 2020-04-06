from celery.utils.log import get_task_logger

from girder.models.file import File
from girder.utility import mail_utils

from isic_archive.celery import app
from isic_archive.models import Dataset, User

logger = get_task_logger(__name__)


@app.task(bind=True)
def applyMetadata(self, datasetId, metadataFileId, userId):
    user = User().load(userId, force=True)
    dataset = Dataset().load(datasetId, force=True)
    metadataFile = File().load(metadataFileId, force=True)
    errors, warnings = Dataset().applyMetadata(
        dataset=dataset, metadataFile=metadataFile, save=True
    )

    # metadata is saved even with warnings
    status = 'Failed' if errors else 'Succeeded'
    subject = f'ISIC Archive: Metadata Application {status} - {dataset["name"]}'
    templateFilename = 'metadataApplication.mako'

    # Mail user
    html = mail_utils.renderTemplate(
        templateFilename,
        {
            'warnings': warnings,
            'errors': errors,
            'user': user,
            'dataset': dataset,
        },
    )
    mail_utils.sendMailSync(
        subject, html, [user['email']] + [u['email'] for u in User().getAdmins()]
    )
