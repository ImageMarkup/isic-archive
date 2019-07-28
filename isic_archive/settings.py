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
