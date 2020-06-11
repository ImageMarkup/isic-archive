import functools

import pytest

from girder.models.setting import Setting
from girder.settings import SettingKey

from isic_archive.models.user import User
from isic_archive.provision_utility import provisionDatabase


@pytest.fixture
def provisionedServer(server):
    provisionDatabase()
    # When the Girder app is mounted at '/', requests to '/api' are able to be routed to the API app
    # Since ISIC mounts the Girder app at `/girder`, requests must be made to the API app directly
    server.request = functools.partial(server.request, appPrefix='/api')
    # Verification emails to new users make it awkward to assert that other ISIC-based features
    # properly send emails
    Setting().set(SettingKey.EMAIL_VERIFICATION, 'disabled')

    # Create the first 'real' user, which will be auto-promoted to admin
    User().createUser(
        login='admin-user',
        password='password',
        firstName='Test',
        lastName='Admin',
        email='test-admin@isic-archive.test'
    )

    yield server
