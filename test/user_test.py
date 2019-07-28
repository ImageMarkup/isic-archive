import pytest
from pytest_girder.assertions import assertStatus, assertStatusOk

from girder.constants import AccessType
from girder.models.group import Group

from isic_archive import IsicArchive, provisionDatabase
from isic_archive.models import User


@pytest.fixture
def provisionedServer(server):
    provisionDatabase()

    # Create the first 'real' user, which will be auto-promoted to admin
    User().createUser(
        login='admin-user',
        password='password',
        firstName='Test',
        lastName='Admin',
        email='test-admin@isic-archive.com'
    )

    yield server


@pytest.mark.plugin('isic_archive', IsicArchive)
def testFirstUserAdmin(provisionedServer):
    # Ensure the first created user is auto-promoted to admin
    adminUser = User().findOne({'login': 'admin-user'})
    assert adminUser['admin'] is True


@pytest.mark.plugin('isic_archive', IsicArchive)
def testBasicUser(provisionedServer):
    # Create a basic user
    resp = provisionedServer.request(path='/user', method='POST', params={
        'email': 'test-user@isic-archive.com',
        'login': 'test-user',
        'firstName': 'test',
        'lastName': 'user',
        'password': 'password'
    })
    assertStatusOk(resp)
    testUser = User().findOne({'login': 'test-user'})
    assert testUser is not None
    # Ensure this user is not auto-promoted
    assert testUser['admin'] is False

    # Ensure creation returns permissions
    negativePermissions = {
        'acceptTerms': False,
        'createDataset': False,
        'reviewDataset': False,
        'segmentationSkill': None,
        'adminStudy': False
    }
    assert resp.json.get('permissions') == negativePermissions

    # Ensure login returns permissions
    resp = provisionedServer.request(path='/user/authentication', method='GET',
                                     basicAuth='test-user:password')
    assertStatusOk(resp)
    assert resp.json['user'].get('permissions') == negativePermissions

    # Ensure get user returns permissions
    resp = provisionedServer.request(path='/user/me', method='GET', user=testUser)
    assertStatusOk(resp)
    assert resp.json.get('permissions') == negativePermissions

    # Ensure get user for anonymous still succeeds
    resp = provisionedServer.request(path='/user/me', method='GET')
    assertStatusOk(resp)
    assert resp.json is None

    # Ensure user is private
    resp = provisionedServer.request(path=f'/user/{testUser["_id"]}', method='GET')
    assertStatus(resp, 401)

    # Ensure accept terms works
    resp = provisionedServer.request(path='/user/acceptTerms', method='POST',
                                     user=testUser)
    assertStatusOk(resp)
    assert resp.json.get('extra') == 'hasPermission'

    resp = provisionedServer.request(path='/user/me', method='GET', user=testUser)
    assertStatusOk(resp)
    acceptedTermsPermissions = negativePermissions.copy()
    acceptedTermsPermissions['acceptTerms'] = True
    assert resp.json.get('permissions') == acceptedTermsPermissions

    # Ensure accepting terms twice is idempotent
    testUser = User().findOne({'login': 'test-user'})
    uploaderUserAcceptTermsTime = testUser['acceptTerms']
    resp = provisionedServer.request(path='/user/acceptTerms', method='POST',
                                     user=testUser)
    assertStatusOk(resp)
    assert resp.json.get('extra') == 'hasPermission'
    testUser = User().findOne({'login': 'test-user'})
    assert testUser['acceptTerms'] == uploaderUserAcceptTermsTime


@pytest.mark.plugin('isic_archive', IsicArchive)
def testUploaderUser(provisionedServer, smtp):
    # Create an uploader admin
    resp = provisionedServer.request(path='/user', method='POST', params={
        'email': 'uploader-admin@isic-archive.com',
        'login': 'uploader-admin',
        'firstName': 'uploader',
        'lastName': 'admin',
        'password': 'password'
    })
    assertStatusOk(resp)
    uploaderAdmin = User().findOne({'login': 'uploader-admin'})
    assert uploaderAdmin is not None
    contributorsGroup = Group().findOne({'name': 'Dataset Contributors'})
    assert contributorsGroup is not None
    Group().addUser(contributorsGroup, uploaderAdmin, level=AccessType.WRITE)

    # Create an uploader user
    resp = provisionedServer.request(path='/user', method='POST', params={
        'email': 'uploader-user@isic-archive.com',
        'login': 'uploader-user',
        'firstName': 'uploader',
        'lastName': 'user',
        'password': 'password'
    })
    assertStatusOk(resp)
    uploaderUser = User().findOne({'login': 'uploader-user'})
    assert uploaderUser is not None

    # TODO: check if a user can upload without agreeing to terms

    # Ensure request create dataset permission works
    resp = provisionedServer.request(path='/user/requestCreateDatasetPermission',
                                     method='POST', user=uploaderUser)
    assertStatusOk(resp)
    assert smtp.waitForMail()
    assert smtp.getMail()  # pop off the queue for later assertion that the queue is empty

    # Ensure that the user can't create datasets yet
    resp = provisionedServer.request(path='/user/me', method='GET', user=uploaderUser)
    assertStatusOk(resp)
    assert not resp.json['permissions']['createDataset']

    # Ensure that a join request is pending
    contributorsGroup = Group().findOne({'name': 'Dataset Contributors'})
    joinRequestUserIds = [user['id'] for user in Group().getFullRequestList(contributorsGroup)]
    assert uploaderUser['_id'] in joinRequestUserIds
    assert smtp.isMailQueueEmpty()

    # Add the user, then ensure they can create datasets
    Group().inviteUser(contributorsGroup, uploaderUser, level=AccessType.READ)
    resp = provisionedServer.request(path='/user/me', method='GET', user=uploaderUser)
    assertStatusOk(resp)
    assert resp.json['permissions']['createDataset']


@pytest.mark.plugin('isic_archive', IsicArchive)
def testReviewerUser(provisionedServer):
    # Create a reviewer user
    resp = provisionedServer.request(path='/user', method='POST', params={
        'email': 'reviewer-user@isic-archive.com',
        'login': 'reviewer-user',
        'firstName': 'reviewer',
        'lastName': 'user',
        'password': 'password'
    })
    assertStatusOk(resp)
    reviewerUser = User().findOne({'login': 'reviewer-user'})
    assert reviewerUser is not None

    # Add the user to the reviewers group
    reviewersGroup = Group().findOne({'name': 'Dataset QC Reviewers'})
    assert reviewersGroup is not None
    Group().addUser(reviewersGroup, reviewerUser, level=AccessType.READ)

    # Ensure they can review datasets
    resp = provisionedServer.request(path='/user/me', method='GET', user=reviewerUser)
    assertStatusOk(resp)
    assert resp.json['permissions']['reviewDataset']


@pytest.mark.plugin('isic_archive', IsicArchive)
def testStudyAdminUser(provisionedServer):
    # Create a study admin user
    resp = provisionedServer.request(path='/user', method='POST', params={
        'email': 'study-admin-user@isic-archive.com',
        'login': 'study-admin-user',
        'firstName': 'study admin',
        'lastName': 'user',
        'password': 'password'
    })
    assertStatusOk(resp)
    studyAdminUser = User().findOne({'login': 'study-admin-user'})
    assert studyAdminUser is not None

    # Add the user to the study admins group
    studyAdminsGroup = Group().findOne({'name': 'Study Administrators'})
    assert studyAdminsGroup is not None
    Group().addUser(studyAdminsGroup, studyAdminUser, level=AccessType.READ)

    # Ensure they can admin studies
    resp = provisionedServer.request(path='/user/me', method='GET', user=studyAdminUser)
    assertStatusOk(resp)
    assert resp.json['permissions']['adminStudy']


@pytest.mark.plugin('isic_archive', IsicArchive)
def testInviteNewUser(provisionedServer, smtp):
    # Create a study admin user
    resp = provisionedServer.request(path='/user', method='POST', params={
        'email': 'study-admin-user@isic-archive.com',
        'login': 'study-admin-user',
        'firstName': 'study admin',
        'lastName': 'user',
        'password': 'password'
    })
    assertStatusOk(resp)
    studyAdminUser = User().findOne({'login': 'study-admin-user'})
    assert studyAdminUser is not None

    # Ensure that user doesn't have permission to invite a new user, yet
    resp = provisionedServer.request(path='/user/invite', method='POST', params={
        'login': 'invited-user',
        'email': 'invited-user@isic-archive.com',
        'firstName': 'invited',
        'lastName': 'user'
    }, user=studyAdminUser)
    assertStatus(resp, 403)

    # Add the user to the study admins group
    studyAdminsGroup = Group().findOne({'name': 'Study Administrators'})
    assert studyAdminsGroup is not None
    Group().addUser(studyAdminsGroup, studyAdminUser, level=AccessType.READ)

    # Ensure that user can invite a new user
    resp = provisionedServer.request(path='/user/invite', method='POST', params={
        'login': 'invited-user',
        'email': 'invited-user@isic-archive.com',
        'firstName': 'invited',
        'lastName': 'user'
    }, user=studyAdminUser)
    assertStatusOk(resp)
    assert 'newUser' in resp.json
    assert 'inviteUrl' in resp.json
    for key in ('login', 'firstName', 'lastName', 'name'):
        assert key in resp.json['newUser']

    assert resp.json['newUser']['login'] == 'invited-user'
    assert resp.json['newUser']['firstName'] == 'invited'
    assert resp.json['newUser']['lastName'] == 'user'
    assert resp.json['newUser']['name']
    assert resp.json['inviteUrl']

    assert smtp.waitForMail()
    assert smtp.getMail()  # pop off the queue for later assertion that the queue is empty

    # Ensure that user can invite a new user and specify the validity period
    resp = provisionedServer.request(path='/user/invite', method='POST', params={
        'login': 'invited-user2',
        'email': 'invited-user2@isic-archive.com',
        'firstName': 'invited',
        'lastName': 'user2',
        'validityPeriod': 15.0
    }, user=studyAdminUser)
    assertStatusOk(resp)
    assert 'newUser' in resp.json
    assert 'inviteUrl' in resp.json
    for key in ('login', 'firstName', 'lastName', 'name'):
        assert key in resp.json['newUser']
    assert resp.json['newUser']['login'] == 'invited-user2'
    assert resp.json['newUser']['firstName'] == 'invited'
    assert resp.json['newUser']['lastName'] == 'user2'
    assert resp.json['newUser']['name']
    assert resp.json['inviteUrl']

    assert smtp.waitForMail()
    assert smtp.getMail()  # pop off the queue for later assertion that the queue is empty

    # Test sending an invalid value for the validity period
    resp = provisionedServer.request(path='/user/invite', method='POST', params={
        'login': 'invited-user3',
        'email': 'invited-user3@isic-archive.com',
        'firstName': 'invited',
        'lastName': 'user3',
        'validityPeriod': 'invalid'
    }, user=studyAdminUser)
    assertStatus(resp, 400)
    assert resp.json['type'] == 'validation'
    assert resp.json.get('field') == 'validityPeriod'
