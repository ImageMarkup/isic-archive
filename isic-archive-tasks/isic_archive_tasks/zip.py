import mimetypes

import os

from celery.utils.log import get_task_logger
import requests

from girder.models.folder import Folder
from girder.models.user import User

from isic_archive_tasks import app, CredentialedGirderTask
from isic_archive_tasks.image import ingestImage


logger = get_task_logger(__name__)

@app.task(bind=True)
def ingestBatchFromZipfile(self, batchId):
    """
    Ingest images from a ZIP file into a dataset.

    The images are extracted to a "Pre-review" folder within the dataset folder.
    """
    from girder.plugins.isic_archive.models.batch import Batch
    from girder.plugins.isic_archive.models.dataset import Dataset
    from girder.plugins.isic_archive.models.image import Image
    from girder.plugins.isic_archive.upload import ZipFileOpener
    from girder.plugins.isic_archive.upload import TempDir
    from girder.plugins.isic_archive.utility.boto import s3

    batch = Batch().load(batchId)
    dataset = Dataset().load(batch['datasetId'], force=True)
    user = User().load(batch['creatorId'], force=True)

    if batch['ingestStatus'] != 'queued':
        raise Exception('Trying to ingest a non-queued batch')

    prereviewFolder = Folder().createFolder(
        parent=Dataset().imagesFolder(dataset),
        name='Pre-review',
        parentType='folder',
        creator=user,
        public=False,
        reuseExisting=True)

    # Get upload information stored on batch
    s3BucketName = batch.get('s3BucketName')
    s3ObjectKey = batch.get('s3ObjectKey')
    if not all([s3BucketName, s3ObjectKey]):
        raise Exception('Error retrieving upload information.')

    # Move file from S3 to the assetstore, attached to the dataset
    with TempDir() as tempDir:
        # Download file from S3 as upload user
        fileName = os.path.join(tempDir, str(batch['_id']) + '.zip')
        s3.download_file(
            Bucket=s3BucketName,
            Key=s3ObjectKey,
            Filename=fileName
        )

        # Attach file to dataset
        # fileSize = os.path.getsize(fileName)
        # with open(fileName, 'rb') as fileStream:
        #     zipFile = Upload().uploadFromFile(
        #         obj=fileStream,
        #         size=fileSize,
        #         name=fileName,
        #         parentType='dataset',
        #         parent=dataset,
        #         attachParent=True,
        #         user=user,
        #         mimeType='application/zip'
        #     )
        # # TODO: remove this once a bug in upstream Girder is fixed
        # zipFile['attachedToType'] = ['dataset', 'isic_archive']
        # set item id to null
        # zipFile = File().save(zipFile)
        # propagatesizechange on the item -filesize

        # Delete file from S3 as upload user
        # s3.delete_object(
        #     Bucket=s3BucketName,
        #     Key=s3ObjectKey
        # )

        batch['ingestStatus'] = 'extracting'
        batch = Batch().save(batch)

        # Process zip file
        with ZipFileOpener(fileName) as (fileList, fileCount):
            for originalFilePath, originalFileRelpath in fileList:
                originalFileName = os.path.basename(originalFileRelpath)
                with open(originalFilePath, 'rb') as originalFileStream:
                    image = Image().createEmptyImage(
                        originalFileRelpath=originalFileRelpath,
                        parentFolder=prereviewFolder,
                        creator=user,
                        dataset=dataset,
                        batch=batch
                    )

                    try:
                        resp = self.session.post('file', params={
                            'parentType': 'item',
                            'parentId': image['_id'],
                            'name': originalFileName,
                            'size': os.path.getsize(originalFilePath),
                            'mimeType': mimetypes.guess_type(originalFileName)[0]
                        }, data=originalFileStream)
                        resp.raise_for_status()
                    except Exception:
                        logger.exception('An individual image failed to be extracted')
                        continue

                ingestImage.delay(image['_id'])

        batch['ingestStatus'] = 'extracted'

        # Remove upload information from batch
        del batch['s3BucketName']
        del batch['s3ObjectKey']
        Batch().save(batch)
