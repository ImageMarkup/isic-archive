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

import six

from girder.exceptions import ValidationException
from girder.utility import setting_utilities


class PluginSettings(object):
    DEMO_MODE = 'isic.demo_mode'
    MAX_ISIC_ID = 'isic.max_isic_id'
    ZIP_UPLOAD_ASSUME_ROLE_DURATION_SECONDS = 'isic.zip_upload_assume_role_duration_seconds'
    ZIP_UPLOAD_ROLE_ARN = 'isic.zip_upload_role_arn'
    ZIP_UPLOAD_S3_BUCKET_NAME = 'isic.zip_upload_s3_bucket_name'
    ZIP_UPLOAD_USER_ACCESS_KEY_ID = 'isic.zip_upload_user_access_key_id'
    ZIP_UPLOAD_USER_SECRET_ACCESS_KEY = 'isic.zip_upload_user_secret_access_key'


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


@setting_utilities.validator(PluginSettings.ZIP_UPLOAD_ASSUME_ROLE_DURATION_SECONDS)
def _validateZipUploadAssumeRoleDurationSeconds(doc):
    if not isinstance(doc['value'], int):
        raise ValidationException('ZIP upload assume role duration must be an integer.', 'value')


@setting_utilities.default(PluginSettings.ZIP_UPLOAD_ASSUME_ROLE_DURATION_SECONDS)
def _defaultZipUploadAssumeRoleDurationSeconds():
    return 3600


@setting_utilities.validator({
    PluginSettings.ZIP_UPLOAD_ROLE_ARN,
    PluginSettings.ZIP_UPLOAD_S3_BUCKET_NAME,
    PluginSettings.ZIP_UPLOAD_USER_ACCESS_KEY_ID,
    PluginSettings.ZIP_UPLOAD_USER_SECRET_ACCESS_KEY
})
def _validateZipUploadSettings(doc):
    if not isinstance(doc['value'], six.string_types):
        descriptions = {
            PluginSettings.ZIP_UPLOAD_ROLE_ARN: 'role ARN',
            PluginSettings.ZIP_UPLOAD_S3_BUCKET_NAME: 'S3 bucket name',
            PluginSettings.ZIP_UPLOAD_USER_ACCESS_KEY_ID: 'user access key ID',
            PluginSettings.ZIP_UPLOAD_USER_SECRET_ACCESS_KEY: 'user secret access key'
        }
        description = descriptions[doc['key']]
        raise ValidationException('ZIP upload %s must be a string.' % description, 'value')


@setting_utilities.default({
    PluginSettings.ZIP_UPLOAD_ROLE_ARN,
    PluginSettings.ZIP_UPLOAD_S3_BUCKET_NAME,
    PluginSettings.ZIP_UPLOAD_USER_ACCESS_KEY_ID,
    PluginSettings.ZIP_UPLOAD_USER_SECRET_ACCESS_KEY
})
def _defaultZipUploadSettings():
    return ''
