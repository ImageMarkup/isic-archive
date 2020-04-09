import io
import os
import subprocess
import tempfile

from bson import ObjectId
from celery import chord
from celery.utils.log import get_task_logger

from girder.models.file import File

from isic_archive import Image
from isic_archive.celery import app
from isic_archive.models.segmentation_helpers import ScikitSegmentationHelper

SUPERPIXEL_VERSION = 3.0
logger = get_task_logger(__name__)


@app.task(bind=True)
def ingestImage(self, imageId):
    image = Image().load(imageId, force=True)

    if image['ingested']:
        logger.warning('Attempting to ingest an already ingested image.')
        return

    try:
        imageFile = Image().originalFile(image)
        originalFileStreamResponse = self.session.get(
            f'file/{imageFile["_id"]}/download',
            allow_redirects=False,
        )
        originalFileStreamResponse.raise_for_status()

        # Scikit-Image is ~70ms faster at decoding image data
        # Note: scikit-image takes custody over the file handle and will close it
        imageData = ScikitSegmentationHelper.loadImage(
            io.BytesIO(originalFileStreamResponse.content)
        )
        image['meta']['acquisition']['pixelsY'] = imageData.shape[0]
        image['meta']['acquisition']['pixelsX'] = imageData.shape[1]
    except Exception:
        logger.exception('Failed to validate image')
        image['readable'] = False
        image['ingested'] = True
        Image().save(image)
        return

    # Store the image stripped of exif metadata
    try:
        with tempfile.NamedTemporaryFile('wb', delete=False) as exifFile:
            exifFile.write(originalFileStreamResponse.content)

        subprocess.check_call(['exiftool', '-All=', exifFile.name])

        base, ext = os.path.splitext(imageFile['name'])
        resp = self.session.post(
            'file',
            params={
                'parentType': 'item',
                'parentId': image['_id'],
                'name': f'{base}.stripped{ext}',
                'size': os.path.getsize(exifFile.name),
                'mimeType': imageFile['mimeType'],
            },
            data=open(exifFile.name, 'rb').read(),
            allow_redirects=False,
        )
        resp.raise_for_status()

        strippedFile = File().load(resp.json()['_id'], force=True)
        strippedFile['stripped'] = True
        File().updateFile(strippedFile)

        # _original will only exist if there was EXIF metadata
        if os.path.exists(f'{exifFile.name}_original'):
            os.unlink(f'{exifFile.name}_original')
    except Exception:
        logger.exception('Failed to strip EXIF metadata from image')
        image['readable'] = False
        image['ingested'] = True
        Image().save(image)
        return

    image['readable'] = True
    image['ingestionState'] = {
        'largeImage': None,
        'superpixelMask': None
    }
    Image().save(image)

    chordHeader = [
        generateSuperpixels.signature(args=(image['_id'],), ignore_result=False),
        generateLargeImage.signature(args=(image['_id'],), ignore_result=False),
    ]
    # make the callback signature immutable, so header results are not passed as an arg
    chordCallback = markImageIngested.signature(
        args=(image['_id'],),
        ignore_result=False,
        immutable=True
    )
    chord(chordHeader)(chordCallback)


@app.task()
def markImageIngested(imageId):
    image = Image().load(imageId, force=True)
    image['ingested'] = True
    Image().save(image)


@app.task(bind=True)
def generateSuperpixels(self, imageId):
    # Temporarily disable superpixel generation for performance
    image = Image().load(imageId, force=True)
    image['ingestionState']['superpixelMask'] = True
    Image().save(image)
    return

    try:
        image = Image().load(imageId, force=True)
        imageFile = Image().originalFile(image)

        originalFileStreamResponse = self.session.get(
            f'file/{imageFile["_id"]}/download',
            allow_redirects=False,
        )
        originalFileStreamResponse.raise_for_status()
        originalFileStreamResponse = io.BytesIO(originalFileStreamResponse.content)

        # Scikit-Image is ~70ms faster at decoding image data
        originalImageData = ScikitSegmentationHelper.loadImage(originalFileStreamResponse)

        superpixelsData = ScikitSegmentationHelper.superpixels(originalImageData)
        superpixelsEncodedStream = ScikitSegmentationHelper.writeImage(
            superpixelsData, 'png')

        uploadSuperpixelsResponse = self.session.post(
            'file',
            params={
                'parentType': 'item',
                'parentId': imageId,
                'name': f'{image["name"]}_superpixels_v{SUPERPIXEL_VERSION}.png',
                'size': len(superpixelsEncodedStream.getvalue()),
                'mimeType': 'image/png'
            },
            data=superpixelsEncodedStream.getvalue(),
            allow_redirects=False,
        )
        uploadSuperpixelsResponse.raise_for_status()

        superpixelsFile = File().load(uploadSuperpixelsResponse.json()['_id'], force=True)
        image = Image().load(imageId, force=True, exc=False)

        superpixelsFile['superpixelVersion'] = SUPERPIXEL_VERSION
        # Work around an upstream Girder bug where "File().validate" sets
        #   superpixelsFile['exts'] = ['0', 'png']
        superpixelsFile['exts'] = ['png']
        superpixelsFile = File().save(superpixelsFile, validate=False)

        image['superpixelsId'] = superpixelsFile['_id']
        image['ingestionState']['superpixelMask'] = True
        Image().save(image)
    except Exception:
        logger.exception('Failed to generate superpixel mask')
        image['ingestionState']['superpixelMask'] = False
        Image().save(image)


@app.task(bind=True)
def generateLargeImage(self, imageId):
    imageItem = Image().load(id=imageId, force=True)
    imageFile = Image().strippedFile(imageItem)

    try:
        originalFileStreamResponse = self.session.get(
            f'file/{imageFile["_id"]}/download',
            allow_redirects=False,
            stream=True,
        )
        originalFileStreamResponse.raise_for_status()

        with tempfile.NamedTemporaryFile() as inputFile, \
            tempfile.NamedTemporaryFile() as outputFile:  # noqa
            inputFile.write(originalFileStreamResponse.content)
            inputFile.flush()  # necessary

            vips_tiffsave(inputFile.name, outputFile.name)

            with open(outputFile.name, 'rb') as vipsResultFile:
                uploadLargeImageResp = self.session.post(
                    'file',
                    params={
                        'parentType': 'item',
                        'parentId': imageId,
                        'name': f'{imageItem["name"]}.tiff',
                        'size': os.path.getsize(outputFile.name)
                    },
                    data=vipsResultFile.read(),
                    allow_redirects=False,
                )
                uploadLargeImageResp.raise_for_status()
    except Exception:
        logger.exception('Failed to create large image')
        imageItem['ingestionState']['largeImage'] = False
        Image().save(imageItem)
        return

    imageItem['largeImage'] = {
        'sourceName': 'tiff',
        'originalId': imageFile['_id'],
        'fileId': ObjectId(uploadLargeImageResp.json()['_id'])
    }
    imageItem['ingestionState']['largeImage'] = True
    Image().save(imageItem)


def vips_tiffsave(infilename, outfilename):
    convert_command = (
        'vips',
        'tiffsave',
        infilename,
        outfilename,
        '--compression', 'jpeg',
        '--Q', '90',
        '--tile',
        '--tile-width', '256',
        '--tile-height', '256',
        '--pyramid',
        '--bigtiff'
    )

    logger.info('running "%s"' % ' '.join(convert_command))
    proc = subprocess.Popen(convert_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = proc.communicate()

    if out.decode().strip():
        logger.info(f'stdout: {out.decode()}')

    if err.decode().strip():
        logger.error(f'stderr: {err.decode()}')

    if proc.returncode:
        raise Exception('VIPS command failed (rc=%d)' % proc.returncode)
