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

from girder.exceptions import ValidationException
from girder.utility import setting_utilities


class PluginSettings(object):
    MAX_ISIC_ID = 'isic.max_isic_id'
    UPLOAD_ROLE_ARN = 'isic.upload_role_arn'
    UPLOAD_BUCKET_NAME = 'isic.upload_bucket_name'


@setting_utilities.validator(PluginSettings.MAX_ISIC_ID)
def _validateMaxIsicIdSetting(doc):
    # TODO: can we disable this from being set via the HTTP API?
    if not isinstance(doc['value'], int):
        raise ValidationException('Maximum ISIC ID must be provided as an integer.', 'value')


@setting_utilities.default(PluginSettings.MAX_ISIC_ID)
def _defaultMaxIsicIdSetting():
    return -1


@setting_utilities.validator({
    PluginSettings.UPLOAD_ROLE_ARN,
    PluginSettings.UPLOAD_BUCKET_NAME
})
def _validateDataUploadSettings(doc):
    if not isinstance(doc['value'], str):
        descriptions = {
            PluginSettings.UPLOAD_ROLE_ARN: 'role ARN',
            PluginSettings.UPLOAD_BUCKET_NAME: 'S3 bucket name'
        }
        description = descriptions[doc['key']]
        raise ValidationException(f'Upload {description} must be a string.', 'value')


@setting_utilities.default({
    PluginSettings.UPLOAD_ROLE_ARN,
    PluginSettings.UPLOAD_BUCKET_NAME
})
def _defaultDataUploadSettings():
    return ''
