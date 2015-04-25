#!/usr/bin/env python
# -*- coding: utf-8 -*-

import csv
import mimetypes
import os
import shutil
import sys
import subprocess
import tempfile
import zipfile

from girder.constants import AccessType
from girder.models.notification import ProgressState
from girder.utility import assetstore_utilities
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


def uploadHandler(event):
    upload_file = event.info['file']
    upload_file_mimetype = upload_file['mimeType']
    if upload_file_mimetype == 'application/octet-stream':
        upload_file_mimetype = mimetypes.guess_type(upload_file['name'], strict=False)[0]
    if upload_file_mimetype not in ZIP_FORMATS + CSV_FORMATS:
        # TODO: check if a non zip or csv is uploaded by a user
        return

    upload_item = ModelImporter.model('item').load(upload_file['itemId'], force=True)
    upload_folder = ModelImporter.model('folder').load(upload_item['folderId'], force=True)
    upload_collection = ModelImporter.model('collection').load(upload_folder['parentId'], force=True)
    if upload_collection['name'] != 'Phase 0':
        return

    upload_file_path = os.path.join(event.info['assetstore']['root'], upload_file['path'])
    upload_user = ModelImporter.model('user').load(upload_item['creatorId'], force=True)

    if upload_folder['name'] == 'dropzip':
        if upload_file_mimetype in ZIP_FORMATS:
            _zipUploadHandler(upload_collection, upload_file, upload_file_path, upload_user)
    else:
        if upload_file_mimetype in CSV_FORMATS:
            _csvUploadHandler(upload_folder, upload_item, upload_file, upload_file_path, upload_user)


class ZipFileOpener(object):
    def __init__(self, zip_file_path):
        self.zip_file_path = zip_file_path
        # TODO: check for "7z" command

    def __enter__(self):
        self._createTempDirs()
        try:
            return self._defaultUnzip()
        except zipfile.BadZipfile:
            return self._fallbackUnzip()


    def _createTempDirs(self):
        assetstore = ModelImporter.model('assetstore').getCurrent()
        assetstore_adapter = assetstore_utilities.getAssetstoreAdapter(assetstore)
        try:
            self.temp_dir = tempfile.mkdtemp(dir=assetstore_adapter.tempDir)
            self.external_temp_dir = tempfile.mkdtemp(dir=assetstore_adapter.tempDir)
        except (AttributeError, OSError):
            self.temp_dir = tempfile.mkdtemp()
            self.external_temp_dir = tempfile.mkdtemp()


    def _defaultUnzip(self):
        zip_file = zipfile.ZipFile(self.zip_file_path)

        # filter out directories and count real files
        file_list = list()
        for original_file in zip_file.infolist():
            original_file_relpath = original_file.filename
            original_file_relpath.replace('\\', '/')
            original_file_name = os.path.basename(original_file_relpath)
            if not original_file_name or not original_file.file_size:
                # file is probably a directory, skip
                continue
            file_list.append((original_file, original_file_relpath))
        return self._defaultUnzipIter(zip_file, file_list), len(file_list), self.external_temp_dir


    def _defaultUnzipIter(self, zip_file, file_list):
        for original_file, original_file_relpath in file_list:
            original_file_name = os.path.basename(original_file_relpath)
            temp_file_path = os.path.join(self.temp_dir, original_file_name)
            with open(temp_file_path, 'wb') as temp_file_obj:
                shutil.copyfileobj(
                    zip_file.open(original_file),
                    temp_file_obj
                )
            yield temp_file_path, original_file_relpath
            os.remove(temp_file_path)
        zip_file.close()


    def _fallbackUnzip(self):
        unzip_command = (
            '7z',
            'x',
            '-y',
            '-o%s' % self.temp_dir,
            self.zip_file_path
        )
        try:
            with open(os.devnull, 'rb') as null_in,\
                    open(os.devnull, 'wb') as null_out:
                subprocess.check_call(unzip_command,
                    stdin=null_in, stdout=null_out, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError:
            self.__exit__(*sys.exc_info())
            raise

        file_list = list()
        for temp_dir_path, _, temp_file_names in os.walk(self.temp_dir):
            for temp_file_name in temp_file_names:
                temp_file_path = os.path.join(temp_dir_path, temp_file_name)
                original_file_relpath = os.path.relpath(temp_file_path, self.temp_dir)
                file_list.append((temp_file_path, original_file_relpath))
        return iter(file_list), len(file_list), self.external_temp_dir


    def __exit__(self, exc_type, exc_val, exc_tb):
        shutil.rmtree(self.temp_dir)
        shutil.rmtree(self.external_temp_dir)


def _uploadFileFromPath(file_path, user, name, parent, parent_type, mime_type):
    upload = ModelImporter.model('upload').createUpload(
        user=user,
        name=name,
        parentType=parent_type,
        parent=parent,
        size=os.path.getsize(file_path),
        mimeType=mime_type,
    )
    with open(file_path, 'rb') as file_obj:
        # TODO: buffered?
        upload_file = ModelImporter.model('upload').handleChunk(
            upload, file_obj.read())
    return upload_file


def _zipUploadHandler(upload_collection, upload_file, upload_file_path, upload_user):
    images_folder = getOrCreateUDAFolder(
        name=os.path.splitext(upload_file['name'])[0],
        description='',
        parent=upload_collection,
        parent_type='collection'
    )
    ModelImporter.model('folder').setUserAccess(images_folder, upload_user, AccessType.ADMIN, save=True)

    with ZipFileOpener(upload_file_path) as (file_list, file_count, temp_dir):
        with ProgressContext(
                on=True,
                user=upload_user,
                title='Processing "%s"' % upload_file['name'],
                total=file_count,
                state=ProgressState.ACTIVE,
                current=0) as progress:

            for original_file_path, original_file_relpath in file_list:
                original_file_name = os.path.basename(original_file_relpath)

                progress.update(
                    increment=1,
                    message='Extracting "%s"' % original_file_name)

                original_file_basename = os.path.splitext(original_file_name)[0]
                converted_file_name = '%s.new.tif' % original_file_basename
                converted_file_path = os.path.join(temp_dir, converted_file_name)

                convert_command = (
                    '/usr/local/bin/vips',
                    'tiffsave',
                    '\'%s\'' % original_file_path,
                    '\'%s\'' % converted_file_path,
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
                #     with open(os.devnull, 'rb') as null_in,\
                #             open(os.devnull, 'wb') as null_out:
                #         subprocess.check_call(convert_command,
                #             stdin=null_in, stdout=null_out, stderr=subprocess.STDOUT)
                # except subprocess.CalledProcessError:
                #     try:
                #         os.remove(converted_file_path)
                #     except OSError:
                #         pass
                #     continue

                # upload original image
                image_file = _uploadFileFromPath(
                    file_path=original_file_path,
                    user=upload_user,
                    name=original_file_name,
                    parent=images_folder,
                    parent_type='folder',
                    mime_type='image/tiff'
                )
                image_item = ModelImporter.model('item').load(image_file['itemId'], force=True)
                image_item['name'] = original_file_basename
                ModelImporter.model('item').updateItem(image_item)

                image_mimetype = mimetypes.guess_type(original_file_relpath)[0]

                # upload converted image
                _uploadFileFromPath(
                    file_path=converted_file_path,
                    user=upload_user,
                    name=converted_file_name,
                    parent=image_item,
                    parent_type='item',
                    mime_type=image_mimetype
                )
                os.remove(converted_file_path)

                ModelImporter.model('item').setMetadata(image_item, {
                    # provide full and possibly-qualified path as originalFilename
                    'originalFilename': original_file_relpath,
                    'originalMimeType': image_mimetype,
                    'convertedFilename': converted_file_name,
                    'convertedMimeType': 'image/tiff',
                })


def _csvUploadHandler(upload_folder, upload_item, upload_file, upload_file_path, upload_user):
    dataset_folder_ids = [
        folder['_id']
        for folder in ModelImporter.model('folder').find({
            'name': upload_folder['name']
        })
    ]
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
