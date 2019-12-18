from girder.models.user import User
from girder.utility import mail_utils

from isic_archive.celery import app
from isic_archive.models import Batch, Dataset
from isic_archive.utility.mail_utils import sendEmailToGroup


@app.task()
def maybeSendIngestionNotifications():
    for batch in Batch().find({'ingestStatus': 'extracted'}):
        if not Batch().hasImagesPendingIngest(batch):
            failedImages = list(Batch().imagesFailedIngest(batch))
            skippedFilenames = list(Batch().imagesSkippedIngest(batch))
            sendIngestionNotification.delay(batch['_id'], failedImages, skippedFilenames)
            batch['ingestStatus'] = 'notified'
            Batch().save(batch)


@app.task()
def sendIngestionNotification(batchId, failedImages, skippedFilenames):
    batch = Batch().load(batchId)
    dataset = Dataset().load(batch['datasetId'], force=True)
    user = User().load(batch['creatorId'], force=True)
    host = mail_utils.getEmailUrlPrefix()
    # TODO: The email should gracefully handle the situation where failedImages or skippedFilenames
    # has an excessive amount of items.
    params = {
        'isOriginalUploader': True,
        'host': host,
        'dataset': dataset,
        # We intentionally leak full user details here, even though all
        # email recipients may not have access permissions to the user
        'user': user,
        'batch': batch,
        'failedImages': failedImages,
        'skippedFilenames': skippedFilenames
    }
    subject = 'ISIC Archive: Dataset Upload Confirmation'
    templateFilename = 'ingestDatasetConfirmation.mako'

    # Mail user
    html = mail_utils.renderTemplate(templateFilename, params)
    mail_utils.sendMailSync(subject, html, user['email'])

    # Mail 'Dataset QC Reviewers' group
    params['isOriginalUploader'] = False
    sendEmailToGroup(
        groupName='Dataset QC Reviewers',
        templateFilename=templateFilename,
        templateParams=params,
        subject=subject,
        asynchronous=False)
