import base64
import datetime
import hashlib

from girder import events
from girder.constants import AccessType
from girder.exceptions import AccessException, ValidationException
from girder.models.group import Group
from girder.models.user import User as GirderUser


class User(GirderUser):
    def initialize(self):
        super(User, self).initialize()

        # Note, this will not expose this field though the upstream User API
        self.exposeFields(level=AccessType.READ, fields=('acceptTerms',))

        events.bind('model.user.save.created',
                    'onUserCreated', self._onUserCreated)

    def _onUserCreated(self, event):
        user = event.info

        # make all users private
        user['public'] = False
        if user['login'] != 'isic-admin':
            self.setGroupAccess(
                doc=user,
                group=Group().findOne({'name': 'Study Administrators'}),
                level=AccessType.READ,
                save=False
            )
        self.save(user)

    def obfuscatedName(self, user):
        # For 4 characters of a Base32 encoding, we have 20 bits of entropy,
        # or 1,048,576 possible combinations. Per the formula at
        # http://preshing.com/20110504/hash-collision-probabilities/
        # and assuming 100 (active) users, we have a collision probability
        # of 0.47%.
        obfuscatedId = base64.b32encode(
            hashlib.sha256(user['login'].encode('utf8')).digest()
        ).decode('ascii')[:4]
        obfuscatedName = f'User {obfuscatedId}'
        return obfuscatedName

    def filterSummary(self, user, accessorUser):
        userSummary = {
            '_id': user['_id'],
            'name': self.obfuscatedName(user)
        }
        if self.hasAccess(user, accessorUser):
            for field in ['login', 'firstName', 'lastName']:
                userSummary[field] = user[field]
        return userSummary

    def _isAdminOrMember(self, user, groupName):
        if not user:
            return False
        if user.get('admin', False):
            return True
        group = Group().findOne({'name': groupName})
        if not group:
            raise ValidationException(f'Could not load group: {groupName}')
        return group['_id'] in user['groups']

    def canAcceptTerms(self, user):
        return user.get('acceptTerms') is not None

    def acceptTerms(self, user):
        user['acceptTerms'] = datetime.datetime.utcnow()

    def requireAcceptTerms(self, user):
        if not self.canAcceptTerms(user):
            raise AccessException(
                'The user has not accepted the Terms of Use.')

    def canCreateDataset(self, user):
        return self._isAdminOrMember(user, 'Dataset Contributors')

    def requireCreateDataset(self, user):
        if not self.canCreateDataset(user):
            raise AccessException(
                'Only members of the Dataset Contributors group can create '
                'datasets.')

    def canReviewDataset(self, user):
        return self._isAdminOrMember(user, 'Dataset QC Reviewers')

    def requireReviewDataset(self, user):
        if not self.canReviewDataset(user):
            raise AccessException(
                'Only members of the Dataset QC Reviewers group can review '
                'datasets.')

    def getSegmentationSkill(self, user):
        # Avoid circular import
        from .segmentation import Segmentation

        if not user:
            return None
        expertGroup = Group().findOne({'name': 'Segmentation Experts'})
        if expertGroup['_id'] in user['groups']:
            return Segmentation().Skill.EXPERT
        noviceGroup = Group().findOne({'name': 'Segmentation Novices'})
        if noviceGroup['_id'] in user['groups']:
            return Segmentation().Skill.NOVICE
        return None

    def requireSegmentationSkill(self, user):
        if self.getSegmentationSkill(user) is None:
            raise AccessException(
                'Only members of the Segmentation Experts and Segmentation '
                'Novices groups can create or review segmentations.')

    def canAdminStudy(self, user):
        return self._isAdminOrMember(user, 'Study Administrators')

    def requireAdminStudy(self, user):
        if not self.canAdminStudy(user):
            raise AccessException(
                'Only members of the Study Administrators group can perform this action.')
