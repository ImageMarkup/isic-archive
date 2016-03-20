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

from girder.models.notification import ProgressState
from girder.utility import assetstore_utilities
from girder.utility.model_importer import ModelImporter
from girder.utility.progress import ProgressContext

from .provision_utility import getAdminUser

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

IMAGE_FORMATS = [
    'image/jpeg',
    'image/png'
    # Do not add TIFF until recursive events are prevented
]


def uploadHandler(event):
    upload_info = {
        'file': event.info['file'],
        'assetstore': event.info['assetstore']
    }

    upload_info['file_mimetype'] = upload_info['file']['mimeType']
    if upload_info['file_mimetype'] == 'application/octet-stream':
        upload_info['file_mimetype'] = mimetypes.guess_type(upload_info['file']['name'], strict=False)[0]

    upload_info['file_path'] = os.path.join(upload_info['assetstore']['root'], upload_info['file']['path'])

    upload_info['item'] = ModelImporter.model('item').load(upload_info['file']['itemId'], force=True)
    upload_info['folder'] = ModelImporter.model('folder').load(upload_info['item']['folderId'], force=True)
    upload_info['collection'] = ModelImporter.model('collection').load(upload_info['folder']['parentId'], force=True)

    upload_info['user'] = ModelImporter.model('user').load(upload_info['item']['creatorId'], force=True)


    if upload_info['collection']['name'] == 'Phase 0':
        if upload_info['folder']['name'] == 'dropzip':
            if upload_info['file_mimetype'] in ZIP_FORMATS:
                _zipUploadHandler(upload_info)
        else:
            if upload_info['file_mimetype'] in IMAGE_FORMATS:
                _imageUploadHandler(upload_info)
            elif upload_info['file_mimetype'] in CSV_FORMATS:
                _csvUploadHandler(upload_info)


class TempDir(object):
    def __init__(self):
        pass

    def __enter__(self):
        assetstore = ModelImporter.model('assetstore').getCurrent()
        assetstore_adapter = assetstore_utilities.getAssetstoreAdapter(assetstore)
        try:
            self.temp_dir = tempfile.mkdtemp(dir=assetstore_adapter.tempDir)
        except (AttributeError, OSError):
            self.temp_dir = tempfile.mkdtemp()
        return self.temp_dir

    def __exit__(self, exc_type, exc_val, exc_tb):
        shutil.rmtree(self.temp_dir)


class ZipFileOpener(object):
    def __init__(self, zip_file_path):
        self.zip_file_path = zip_file_path
        # TODO: check for "7z" command

    def __enter__(self):
        try:
            return self._defaultUnzip()
        except zipfile.BadZipfile:
            return self._fallbackUnzip()

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

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
        return self._defaultUnzipIter(zip_file, file_list), len(file_list)


    def _defaultUnzipIter(self, zip_file, file_list):
        with TempDir() as temp_dir:
            for original_file, original_file_relpath in file_list:
                original_file_name = os.path.basename(original_file_relpath)
                temp_file_path = os.path.join(temp_dir, original_file_name)
                with open(temp_file_path, 'wb') as temp_file_obj:
                    shutil.copyfileobj(
                        zip_file.open(original_file),
                        temp_file_obj
                    )
                yield temp_file_path, original_file_relpath
                os.remove(temp_file_path)
            zip_file.close()


    def _fallbackUnzip(self):
        with TempDir() as temp_dir:
            unzip_command = (
                '7z',
                'x',
                '-y',
                '-o%s' % temp_dir,
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
            for temp_dir_path, _, temp_file_names in os.walk(temp_dir):
                for temp_file_name in temp_file_names:
                    temp_file_path = os.path.join(temp_dir_path, temp_file_name)
                    original_file_relpath = os.path.relpath(temp_file_path, temp_dir)
                    file_list.append((temp_file_path, original_file_relpath))
            return iter(file_list), len(file_list)


def _zipUploadHandler(upload_info):
    images_folder = ModelImporter.model('folder').createFolder(
        parent=upload_info['collection'],
        name=os.path.splitext(upload_info['file']['name'])[0],
        description='',
        parentType='collection',
        creator=upload_info['user']
    )

    with ZipFileOpener(upload_info['file_path']) as (file_list, file_count):
        with ProgressContext(
                on=True,
                user=upload_info['user'],
                title='Processing "%s"' % upload_info['file']['name'],
                total=file_count,
                state=ProgressState.ACTIVE,
                current=0) as progress:

            for original_file_path, original_file_relpath in file_list:
                original_file_name = os.path.basename(original_file_relpath)

                progress.update(
                    increment=1,
                    message='Extracting "%s"' % original_file_name)

                image_item = ModelImporter.model('image', 'isic_archive').createImage(
                    creator=upload_info['user'],
                    parentFolder=images_folder
                )

                # upload original image
                image_mimetype = mimetypes.guess_type(original_file_name)[0]
                with open(original_file_path, 'rb') as original_file_obj:
                    ModelImporter.model('upload').uploadFromFile(
                        obj=original_file_obj,
                        size=os.path.getsize(original_file_path),
                        name='%s%s' % (
                            image_item['name'],
                            os.path.splitext(original_file_name)[1]
                        ),
                        parentType='item',
                        parent=image_item,
                        user=upload_info['user'],
                        mimeType=image_mimetype,
                    )

                ModelImporter.model('image', 'isic_archive').setMetadata(image_item, {
                    # provide full and possibly-qualified path as originalFilename
                    'originalFilename': original_file_relpath
                })


def _imageUploadHandler(upload_info):
    image_item = upload_info['item']

    with TempDir() as temp_dir:
        converted_file_name = '%s.tif' % image_item['name']
        converted_file_path = os.path.join(temp_dir, converted_file_name)

        convert_command = (
            '/usr/local/bin/vips',
            'tiffsave',
            '\'%s\'' % upload_info['file_path'],
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

        # upload converted image
        with open(converted_file_path, 'rb') as converted_file_obj:
            converted_file = ModelImporter.model('upload').uploadFromFile(
                obj=converted_file_obj,
                size=os.path.getsize(converted_file_path),
                name=converted_file_name,
                parentType='item',
                parent=image_item,
                user=upload_info['user'],
                mimeType='image/tiff',
            )
        os.remove(converted_file_path)

        image_item['meta']['convertedFilename'] = converted_file_name
        image_item['largeImage'] = converted_file['_id']
        image_item['largeImageSourceName'] = 'tiff'
        ModelImporter.model('image', 'isic_archive').save(image_item)


def _csvUploadHandler(upload_info):
    dataset_folder_ids = [
        folder['_id']
        for folder in ModelImporter.model('folder').find({
            'name': upload_info['folder']['name']
        })
    ]
    # TODO: ensure that dataset_folder_ids are UDA folders / in UDA phases

    parse_errors = list()
    with open(upload_info['file_path'], 'rUb') as upload_file_obj,\
        ProgressContext(
            on=True,
            user=upload_info['user'],
            title='Processing "%s"' % upload_info['file']['name'],
            state=ProgressState.ACTIVE,
            message='Parsing CSV') as progress:

        # csv.reader(csvfile, delimiter=',', quotechar='"')
        csv_reader = csv.DictReader(upload_file_obj)

        if 'isic_id' not in csv_reader.fieldnames:
            # TODO: error
            return

        for csv_row in csv_reader:
            isic_id = csv_row.pop('isic_id', None)
            if not isic_id:
                parse_errors.append('No "isic_id" field in row %d' % csv_reader.line_num)
                continue

            # TODO: require upload_info['user'] to match image creator?
            image_items = ModelImporter.model('image', 'isic_archive').find({
                'name': isic_id,
                'folderId': {'$in': dataset_folder_ids}
            })
            if not image_items.count():
                parse_errors.append('No image found with isic_id "%s"' % isic_id)
                continue
            elif image_items.count() > 1:
                parse_errors.append('Multiple images found with isic_id "%s"' % isic_id)
                continue
            else:
                image_item = image_items.next()

            clinical_metadata = image_item['meta']['clinical']
            clinical_metadata.update(csv_row)
            ModelImporter.model('image', 'isic_archive').setMetadata(image_item, {
                'clinical': clinical_metadata
            })

    if parse_errors:
        # TODO: eventually don't store whole string in memory
        parse_errors_str = '\n'.join(parse_errors)

        upload = ModelImporter.model('upload').createUpload(
            user=getAdminUser(),
            name='parse_errors.txt',
            parentType='item',
            parent=upload_info['item'],
            size=len(parse_errors_str),
            mimeType='text/plain',
        )
        ModelImporter.model('upload').handleChunk(
            upload, parse_errors_str)
