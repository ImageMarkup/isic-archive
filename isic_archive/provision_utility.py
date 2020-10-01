from girder.constants import AccessType
from girder.models.assetstore import Assetstore
from girder.models.collection import Collection
from girder.models.folder import Folder
from girder.models.group import Group
from girder.models.setting import Setting
from girder.settings import SettingKey
from girder_large_image.constants import PluginSettings as LargeImageSettings

from isic_archive import settings
from .models.user import User


def getAdminUser():
    # TODO: cache this?
    return User().findOne({'login': 'isic-admin'})


def _setGirderSettings():
    Setting().set(SettingKey.USER_DEFAULT_FOLDERS, 'none')
    Setting().set(SettingKey.CONTACT_EMAIL_ADDRESS, 'admin@isic-archive.com')
    Setting().set(SettingKey.BRAND_NAME, 'ISIC Archive')
    # TODO: Make email verification required when not in development
    Setting().set(SettingKey.EMAIL_VERIFICATION, 'optional')
    # TODO: restart after ROUTE_TABLE is set?
    Setting().set(SettingKey.ROUTE_TABLE, {
        'core_girder': '/girder',
        'core_static_root': '/static',
        'markup': '/markup',
    })

    Setting().set(SettingKey.CORS_ALLOW_ORIGIN, ','.join(settings.ISIC_CORS_ORIGINS))
    Setting().set(SettingKey.CORS_ALLOW_METHODS, 'HEAD, GET, POST, PUT, DELETE')

    Setting().set(SettingKey.EMAIL_HOST, settings.ISIC_GIRDER_SITE_URL)

    for isicSettingValue, girderSettingKey in [
        (settings.ISIC_SMTP_HOST, SettingKey.SMTP_HOST),
        (settings.ISIC_SMTP_PORT, SettingKey.SMTP_PORT),
        (settings.ISIC_SMTP_USERNAME, SettingKey.SMTP_USERNAME),
        (settings.ISIC_SMTP_PASSWORD, SettingKey.SMTP_PASSWORD),
        (settings.ISIC_SMTP_ENCRYPTION, SettingKey.SMTP_ENCRYPTION),
    ]:
        if isicSettingValue is not None:
            Setting().set(girderSettingKey, isicSettingValue)


def _setLargeImageSettings():
    Setting().set(LargeImageSettings.LARGE_IMAGE_AUTO_SET, False)
    Setting().set(LargeImageSettings.LARGE_IMAGE_MAX_SMALL_IMAGE_SIZE, 0)
    # TODO: consider saving thumbnail files
    Setting().set(LargeImageSettings.LARGE_IMAGE_MAX_THUMBNAIL_FILES, 0)


def _provisionAdminUser():
    adminUser = User().findOne({'login': 'isic-admin'})
    if not adminUser:
        adminUser = User().createUser(
            login='isic-admin',
            password=None,
            firstName='ISIC Archive',
            lastName='Admin',
            email='admin@isic-archive.test',
            admin=True,
            public=False,
        )

    if settings.ISIC_ADMIN_PASSWORD:
        User().setPassword(adminUser, settings.ISIC_ADMIN_PASSWORD, save=False)
        adminUser['status'] = 'enabled'
        User().save(adminUser)
    else:
        User().setPassword(adminUser, None, save=False)
        adminUser['status'] = 'disabled'
        # TODO: subsequent re-saves of this user will re-enable it, until another user is created
        adminUser = User().save(adminUser, validate=False)


def _provisionAssetstore():
    if not Assetstore().findOne({'name': 'assetstore'}):
        if not settings.ISIC_ASSETSTORE_PATH.is_dir():
            # This is expected to fail if the path is owned by root
            settings.ISIC_ASSETSTORE_PATH.mkdir(parents=True)
        Assetstore().createFilesystemAssetstore(
            name='assetstore',
            root=str(settings.ISIC_ASSETSTORE_PATH.resolve()),
        )


def _provisionImages():
    if not Group().findOne({'name': 'Dataset Contributors'}):
        contributorsGroup = Group().createGroup(
            name='Dataset Contributors',
            creator=getAdminUser(),
            description='Users that can create datasets',
            public=True
        )
        Group().removeUser(contributorsGroup, getAdminUser())

    reviewerGroup = Group().findOne({'name': 'Dataset QC Reviewers'})
    if not reviewerGroup:
        reviewerGroup = Group().createGroup(
            name='Dataset QC Reviewers',
            creator=getAdminUser(),
            description='Users responsible for doing initial QC',
            public=True
        )
        Group().removeUser(reviewerGroup, getAdminUser())

    if not Collection().findOne({'name': 'Flagged Images'}):
        flaggedCollection = Collection().createCollection(
            name='Flagged Images',
            creator=getAdminUser(),
            description='Images that have been flagged for any reason',
            public=False,
            reuseExisting=False
        )
        flaggedCollection = Collection().setAccessList(
            doc=flaggedCollection,
            access={},
            save=False
        )
        Collection().setGroupAccess(
            doc=flaggedCollection,
            group=reviewerGroup,
            # TODO: make this a special access level
            level=AccessType.READ,
            save=True
        )

    imageCollection = Collection().createCollection(
        name='Lesion Images',
        creator=getAdminUser(),
        description='All public lesion image datasets',
        public=True,
        reuseExisting=True
    )
    Collection().setAccessList(
        doc=imageCollection,
        access={},
        save=True
    )


def _provisionSegmentationGroups():
    if not Group().findOne({'name': 'Segmentation Novices'}):
        segmentationNovicesGroup = Group().createGroup(
            name='Segmentation Novices',
            creator=getAdminUser(),
            description='Users able to tentatively segment lesion boundaries',
            public=True
        )
        Group().removeUser(segmentationNovicesGroup, getAdminUser())

    if not Group().findOne({'name': 'Segmentation Experts'}):
        segmentationExpertsGroup = Group().createGroup(
            name='Segmentation Experts',
            creator=getAdminUser(),
            description='Users able to definitively segment lesion boundaries',
            public=True
        )
        Group().removeUser(segmentationExpertsGroup, getAdminUser())


def _provisionStudies():
    studyAdminGroup = Group().findOne({'name': 'Study Administrators'})
    if not studyAdminGroup:
        studyAdminGroup = Group().createGroup(
            name='Study Administrators',
            creator=getAdminUser(),
            description='Annotation study creators and administrators',
            public=True
        )
        Group().removeUser(studyAdminGroup, getAdminUser())

    studiesCollection = Collection().createCollection(
        name='Annotation Studies',
        creator=getAdminUser(),
        description='Clinical feature annotation studies',
        public=True,
        reuseExisting=True
    )
    studiesCollection = Collection().setAccessList(
        doc=studiesCollection,
        access={},
        save=False
    )
    Collection().setGroupAccess(
        doc=studiesCollection,
        group=studyAdminGroup,
        # TODO: make this a special access level
        level=AccessType.READ,
        save=True
    )


def _provisionTemporaryUploads():
    uploadCollection = Collection().createCollection(
        name='Temporary ZIP Uploads',
        creator=getAdminUser(),
        description='Temporary holding area for uploaded ZIP files',
        public=False,
        reuseExisting=True
    )
    uploadCollection = Collection().setAccessList(
        doc=uploadCollection,
        access={},
        save=True
    )

    uploadFolder = Folder().createFolder(
        name='Temporary ZIP Uploads',
        parentType='collection',
        parent=uploadCollection,
        creator=getAdminUser(),
        public=False,
        reuseExisting=True
    )
    Folder().setAccessList(
        doc=uploadFolder,
        access={},
        save=True
    )


def provisionDatabase():
    _setGirderSettings()
    _setLargeImageSettings()
    _provisionAdminUser()
    _provisionAssetstore()
    _provisionImages()
    _provisionSegmentationGroups()
    _provisionStudies()
    _provisionTemporaryUploads()
