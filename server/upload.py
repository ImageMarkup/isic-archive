# coding=utf-8

import csv
import mimetypes
import os
import shutil
import subprocess
import tempfile
import zipfile

from girder.constants import AccessType
from girder.models.notification import ProgressState
from girder.utility.model_importer import ModelImporter
from girder.utility.progress import ProgressContext

from .provision_utility import getOrCreateUDAFolder, getAdminUser

ZIP_FORMATS = [
    'multipart/x-zip',
    'application/zip',
    'application/zip-compressed',
    'application/x-zip-compressed',
]

CSV_FORMATS = [
    'text/csv',
    'application/vnd.ms-excel'
]


class TemporaryDirectory(object):
    def __enter__(self):
        self.temp_dir = tempfile.mkdtemp()
        return self.temp_dir

    def __exit__(self, exc_type, exc_val, exc_tb):
        shutil.rmtree(self.temp_dir)


def uploadHandler(event):
    upload_file = event.info['file']
    upload_item = ModelImporter.model('item').load(upload_file['itemId'], force=True)
    upload_folder = ModelImporter.model('folder').load(upload_item['folderId'], force=True)
    upload_collection = ModelImporter.model('collection').load(upload_folder['parentId'], force=True)

    if upload_collection['name'] != 'Phase 0':
        return

    upload_file_mimetype = upload_file['mimeType']
    if upload_file_mimetype == 'application/octet-stream':
        upload_file_mimetype = mimetypes.guess_type(upload_file['name'], strict=False)[0]

    upload_file_path = os.path.join(event.info['assetstore']['root'], upload_file['path'])
    upload_user = ModelImporter.model('user').load(upload_item['creatorId'], force=True)

    if upload_folder['name'] == 'dropzip':
        if upload_file_mimetype in ZIP_FORMATS:
            zipUploadHandler(upload_collection, upload_file, upload_file_path, upload_user)
        else:
            pass
            # TODO: warning
    else:
        if upload_file_mimetype in CSV_FORMATS:
            csvUploadHandler(upload_folder, upload_item, upload_file, upload_file_path, upload_user)
        else:
            pass
            # TODO: warning


def zipUploadHandler(upload_collection, upload_file, upload_file_path, upload_user):
    images_folder = getOrCreateUDAFolder(
        name=os.path.splitext(upload_file['name'])[0],
        description='',
        parent=upload_collection,
        parent_type='collection'
    )
    ModelImporter.model('folder').setUserAccess(images_folder, upload_user, AccessType.ADMIN, save=True)

    with zipfile.ZipFile(upload_file_path) as zip_file:
        # filter out directories and count real files
        zip_files = list()
        for original_file in zip_file.infolist():
            original_file_name = original_file.filename
            original_file_name.replace('\\', '/')
            original_file_name = os.path.basename(original_file_name)
            if not original_file_name or not original_file.file_size:
                # file is probably a directory, skip
                continue
            zip_files.append((original_file, original_file_name))

        with TemporaryDirectory() as temp_dir, \
            ProgressContext(
                on=True,
                user=upload_user,
                title='Processing "%s"' % upload_file['name'],
                total=len(zip_files),
                state=ProgressState.ACTIVE,
                current=0) as progress:

            for original_file, original_file_name in zip_files:
                progress.update(
                    increment=1,
                    message='Extracting "%s"' % original_file_name)

                original_file_path = os.path.join(temp_dir, original_file_name)
                with open(original_file_path, 'wb') as original_file_obj:
                    shutil.copyfileobj(
                        zip_file.open(original_file),
                        original_file_obj
                    )

                original_file_basename = os.path.splitext(original_file_name)[0]
                converted_file_name = '%s.new.tif' % original_file_basename
                converted_file_path = os.path.join(temp_dir, converted_file_name)

                convert_command = (
                    '/usr/local/bin/vips',
                    'tiffsave',
                    original_file_path, converted_file_path,
                    '--compression', 'jpeg',
                    '--Q', '90',
                    '--tile',
                    '--tile-width', '256',
                    '--tile-height', '256',
                    '--pyramid',
                    '--bigtiff',
                )
                # TODO: subprocess.check_call is causing the whole application to crash
                os.popen(' '.join(convert_command))
                # try:
                #     subprocess.check_call(convert_command)
                # except subprocess.CalledProcessError:
                #     os.remove(original_file_path)
                #     try:
                #         os.remove(converted_file_path)
                #     except OSError:
                #         pass
                #     continue

                # upload original image
                upload = ModelImporter.model('upload').createUpload(
                    user=upload_user,
                    name=original_file_name,
                    parentType='folder',
                    parent=images_folder,
                    size=os.path.getsize(original_file_path),
                    mimeType='image/tiff',
                )
                with open(original_file_path, 'rb') as original_file_obj:
                    # TODO: buffered?
                    image_file = ModelImporter.model('upload').handleChunk(
                        upload, original_file_obj.read())
                os.remove(original_file_path)

                image_item = ModelImporter.model('item').load(image_file['itemId'], force=True)
                image_item['name'] = original_file_basename
                ModelImporter.model('item').updateItem(image_item)

                image_mimetype = mimetypes.guess_type(original_file.filename)[0]

                # upload converted image
                upload = ModelImporter.model('upload').createUpload(
                    user=upload_user,
                    name=converted_file_name,
                    parentType='item',
                    parent=image_item,
                    size=os.path.getsize(converted_file_path),
                    mimeType=image_mimetype,
                )
                with open(converted_file_path, 'rb') as converted_file_obj:
                    # TODO: buffered?
                    ModelImporter.model('upload').handleChunk(
                        upload, converted_file_obj.read())
                os.remove(converted_file_path)

                ModelImporter.model('item').setMetadata(image_item, {
                    # provide full and possibly-qualified path as originalFilename
                    'originalFilename': original_file.filename,
                    'originalMimeType': image_mimetype,
                    'convertedFilename': converted_file_name,
                    'convertedMimeType': 'image/tiff',
                })


def csvUploadHandler(upload_folder, upload_item, upload_file, upload_file_path, upload_user):
    dataset_folder_ids = [
        folder['_id']
        for folder in ModelImporter.model('folder').find({
            'name': upload_folder['name']
    })]
    # TODO: ensure that dataset_folder_ids are UDA folders / in UDA phases

    parse_errors = list()
    with open(upload_file_path, 'rUb') as upload_file_obj,\
        ProgressContext(
            on=True,
            user=upload_user,
            title='Processing "%s"' % upload_file['name'],
            state=ProgressState.ACTIVE,
            message='Parsing CSV') as progress:

        # csv.reader(csvfile, delimiter=',', quotechar='"')
        csv_reader = csv.DictReader(upload_file_obj)

        if 'isic_id' not in csv_reader.fieldnames:
            # TODO: error
            return

        for csv_row in csv_reader:
            isic_id = csv_row['isic_id']
            if not isic_id:
                parse_errors.append('No "isic_id" field in row %d' % csv_reader.line_num)
                continue

            # TODO: require upload_user to match image creator?
            image_items = ModelImporter.model('item').find({
                'name': '%s.tif' % isic_id,
                'parentId': {'$in': dataset_folder_ids}
            })
            if not image_items.count():
                parse_errors.append('No image found with isic_id "%s"' % isic_id)
                continue
            elif image_items.count() > 1:
                parse_errors.append('Multiple images found with isic_id "%s"' % isic_id)
                continue
            else:
                image_item = image_items.next()

            ModelImporter.model('item').setMetadata(image_item, metadata=csv_row)

    if parse_errors:
        # TODO: eventually don't store whole string in memory
        parse_errors_str = '\n'.join(parse_errors)

        upload = ModelImporter.model('upload').createUpload(
            user=getAdminUser(),
            name='parse_errors.txt',
            parentType='item',
            parent=upload_item,
            size=len(parse_errors_str),
            mimeType='text/plain',
        )
        ModelImporter.model('upload').handleChunk(
            upload, parse_errors_str)
