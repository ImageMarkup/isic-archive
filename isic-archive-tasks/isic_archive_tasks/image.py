import io
import os
import re
import subprocess
import tempfile
import time

from bson import ObjectId
from celery import chord
from celery.utils.log import get_task_logger
import requests
import sentry_sdk

from girder.models.file import File

from isic_archive_tasks import app, CredentialedGirderTask


SUPERPIXEL_VERSION = 3.0
logger = get_task_logger(__name__)


@app.task()
def ingestImage(imageId):
    from girder.plugins.isic_archive.models.image import Image
    image = Image().load(imageId, force=True)

    if image['ingested']:
        logger.warning('Attempting to ingest an already ingested image.')
        return

    try:
        imageData = Image().imageData(image)
        image['meta']['acquisition']['pixelsY'] = imageData.shape[0]
        image['meta']['acquisition']['pixelsX'] = imageData.shape[1]
    except Exception:
        logger.exception('Failed to validate image')
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

    callback = markImageIngested.s(image['_id'])
    chord([generateSuperpixels.s(image['_id']),
           generateLargeImage.s(image['_id'])])(callback)


@app.task()
def markImageIngested(results, imageId):
    from girder.plugins.isic_archive.models.image import Image
    image = Image().load(imageId, force=True)
    image['ingested'] = True
    Image().save(image)


@app.task(bind=True)
def generateSuperpixels(self, imageId):
    try:
        from girder.plugins.isic_archive.models.image import Image
        from girder.plugins.isic_archive.models.segmentation_helpers.scikit import \
            ScikitSegmentationHelper
        image = Image().load(imageId, force=True)
        imageFile = Image().originalFile(image)

        originalFileStreamResponse = self.session.get(
            'file/%s/download' % imageFile['_id'])
        originalFileStreamResponse.raise_for_status()
        originalFileStreamResponse = io.BytesIO(originalFileStreamResponse.content)

        # Scikit-Image is ~70ms faster at decoding image data
        originalImageData = ScikitSegmentationHelper.loadImage(originalFileStreamResponse)

        superpixelsData = ScikitSegmentationHelper.superpixels(originalImageData)
        superpixelsEncodedStream = ScikitSegmentationHelper.writeImage(
            superpixelsData, 'png')

        uploadSuperpixelsResponse = self.session.post('file', params={
            'parentType': 'item',
            'parentId': imageId,
            'name': '%s_superpixels_v%s.png' % (image['name'], SUPERPIXEL_VERSION),
            'size': len(superpixelsEncodedStream.getvalue()),
            'mimeType': 'image/png'
        }, data=superpixelsEncodedStream.getvalue())
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
    from girder.plugins.isic_archive.models.image import Image
    from girder.plugins.large_image.models.image_item import ImageItem
    imageItem = ImageItem().load(id=imageId, force=True)
    imageFile = Image().originalFile(imageItem)

    # todo url
    try:
        originalFileStreamResponse = self.session.get(
            'file/%s/download' % imageFile['_id'], stream=True)
        originalFileStreamResponse.raise_for_status()

        with tempfile.NamedTemporaryFile() as inputFile, \
            tempfile.NamedTemporaryFile() as outputFile:
            inputFile.write(originalFileStreamResponse.content)
            inputFile.flush()  # necessary

            vips_tiffsave(inputFile.name, outputFile.name)

            with open(outputFile.name) as vipsResultFile:
                uploadLargeImageResp = self.session.post(
                    'file',
                    params={
                        'parentType': 'item',
                        'parentId': imageId,
                        'name': imageItem['name'] + '.tiff',
                        'size': os.path.getsize(outputFile.name)
                    }, data=vipsResultFile.read(),
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
    ImageItem().save(imageItem)

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

    if out.strip():
        logger.info('stdout: ' + out)

    if err.strip():
        logger.error('stderr: ' + err)

    if proc.returncode:
        raise Exception('VIPS command failed (rc=%d)' % proc.returncode)
