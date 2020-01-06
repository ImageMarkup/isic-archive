from functools import partial
import mimetypes
import os

from celery.utils.log import get_task_logger

from girder.models.collection import Collection
from girder.models.file import File
from girder.models.folder import Folder
from girder.models.item import Item
from girder.models.user import User

from isic_archive.celery import app
from isic_archive.models import Batch, Dataset, Image
from isic_archive.upload import TempDir, ZipFileOpener
from isic_archive.utility.boto import s3

logger = get_task_logger(__name__)


def _uploadZipfileToGirder(requestSession, filePath, dataset):
    # Attach file to dataset
    uploadCollection = Collection().findOne({
        'name': 'Temporary ZIP Uploads'
    })
    uploadFolder = Folder().findOne({
        'name': 'Temporary ZIP Uploads',
        'baseParentId': uploadCollection['_id']
    })

    fileSize = os.path.getsize(filePath)
    with open(filePath, 'rb') as fileStream:
        uploadFileResponse = requestSession.post(
            'file',
            params={
                'parentType': 'folder',
                'parentId': uploadFolder['_id'],
                'name': filePath,
                'size': fileSize,
                'mimeType': 'application/zip'
            },
        )
        uploadFileResponse.raise_for_status()
        uploadId = uploadFileResponse.json()['_id']

        chunk_size = 1024 * 1024 * 50
        offset = 0
        for chunk in iter(partial(fileStream.read, chunk_size), b''):
            uploadChunkResponse = requestSession.post('file/chunk',
                                                      params={'offset': offset,
                                                              'uploadId': uploadId},
                                                      data=chunk)
            uploadChunkResponse.raise_for_status()
            offset += len(chunk)

    uploadFile = File().load(uploadChunkResponse.json()['_id'], force=True)
    uploadItem = Item().load(uploadFile['itemId'], force=True)

    uploadFile['itemId'] = None
    uploadFile['attachedToType'] = ['dataset', 'isic_archive']
    uploadFile['attachedToId'] = dataset['_id']
    uploadFile = File().save(uploadFile)

    File().propagateSizeChange(
        item=uploadItem,
        sizeIncrement=-uploadFile['size'],
        updateItemSize=False
    )
    Item().remove(uploadItem)

    return uploadFile


@app.task(bind=True)
def ingestBatchFromZipfile(self, batchId):
    """
    Ingest images from a ZIP file into a dataset.

    The images are extracted to a "Pre-review" folder within the dataset folder.
    """
    from isic_archive.tasks import ingestImage
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
        filePath = os.path.join(tempDir, f'{batch["_id"]}.zip')
        s3.download_file(
            Bucket=s3BucketName,
            Key=s3ObjectKey,
            Filename=filePath
        )

        uploadFile = _uploadZipfileToGirder(self.session, filePath, dataset)

        # Delete file from S3 as upload user
        s3.delete_object(
            Bucket=s3BucketName,
            Key=s3ObjectKey
        )

        batch['ingestStatus'] = 'extracting'
        batch['uploadFileId'] = uploadFile['_id']
        batch = Batch().save(batch)

        # Process zip file
        with ZipFileOpener(filePath) as (fileList, fileCount):
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
                            'name': '%s%s' % (
                                image['name'],
                                os.path.splitext(originalFileName)[1].lower()
                            ),
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
