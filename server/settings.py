#!/usr/bin/env python
# -*- coding: utf-8 -*-

###############################################################################
#  Copyright Kitware Inc.
#
#  Licensed under the Apache License, Version 2.0 ( the "License" );
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
###############################################################################

from girder.constants import AssetstoreType
from girder.exceptions import ValidationException
from girder.models.assetstore import Assetstore
from girder.utility import setting_utilities


class PluginSettings(object):
    DEMO_MODE = 'isic.demo_mode'
    MAX_ISIC_ID = 'isic.max_isic_id'
    ZIP_UPLOAD_S3_ASSETSTORE_ID = 'isic.zip_upload_s3_assetstore_id'


@setting_utilities.validator(PluginSettings.DEMO_MODE)
def _validateDemoModeSetting(doc):
    if not isinstance(doc['value'], bool):
        raise ValidationException('Demo mode must be provided as a boolean.', 'value')


@setting_utilities.default(PluginSettings.DEMO_MODE)
def _defaultDemoModeSetting():
    return False


@setting_utilities.validator(PluginSettings.MAX_ISIC_ID)
def _validateMaxIsicIdSetting(doc):
    # TODO: can we disable this from being set via the HTTP API?
    if not isinstance(doc['value'], int):
        raise ValidationException('Maximum ISIC ID must be provided as an integer.', 'value')


@setting_utilities.default(PluginSettings.MAX_ISIC_ID)
def _defaultMaxIsicIdSetting():
    return -1


@setting_utilities.validator(PluginSettings.ZIP_UPLOAD_S3_ASSETSTORE_ID)
def _validateZipUploadS3AssetstoreId(doc):
    # Allow clearing setting
    if not doc['value']:
        return

    # Require S3 assetstore
    assetstore = Assetstore().load(doc['value'], exc=False)
    if assetstore is None:
        raise ValidationException('Invalid assetstore ID.', 'value')
    if assetstore['type'] != AssetstoreType.S3:
        raise ValidationException('ZIP upload assetstore must be an S3 assetstore.', 'value')


@setting_utilities.default(PluginSettings.ZIP_UPLOAD_S3_ASSETSTORE_ID)
def _defaultZipUploadS3AssetstoreId():
    return None
