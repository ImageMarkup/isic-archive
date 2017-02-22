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

import os
import time

from six.moves import queue

from girder.constants import ROOT_DIR, SettingKey
from tests import base


class IsicTestCase(base.TestCase):
    def setUp(self, drop=False):
        Assetstore = self.model('assetstore')
        Setting = self.model('setting')

        if drop:
            base.dropTestDatabase(dropModels=True)

        assetstoreName = os.environ.get('GIRDER_TEST_ASSETSTORE', 'test')
        assetstorePath = os.path.join(
            ROOT_DIR, 'tests', 'assetstore', assetstoreName)
        if drop:
            base.dropFsAssetstore(assetstorePath)
        if not Assetstore.find({'name': 'Test'}).count():
            self.assetstore = Assetstore.createFilesystemAssetstore(
                name='Test', root=assetstorePath)

        addr = ':'.join(map(str, base.mockSmtp.address or ('localhost', 25)))
        Setting.set(SettingKey.SMTP_HOST, addr)
        Setting.set(SettingKey.UPLOAD_MINIMUM_CHUNK_SIZE, 0)
        Setting.set(SettingKey.PLUGINS_ENABLED, base.enabledPlugins)

    def assertNoMail(self):
        """Assert that the email queue is empty."""
        self.assertTrue(base.mockSmtp.isMailQueueEmpty())

    def assertMails(self, count=1, timeout=10):
        """
        Assert that emails have been sent.

        :param count: The number of emails.
        :param timeout: Timeout in seconds.
        """
        remaining = count
        startTime = time.time()
        while remaining > 0:
            if base.mockSmtp.waitForMail():
                try:
                    while base.mockSmtp.getMail():
                        remaining -= 1
                except queue.Empty:
                    pass

            if time.time() > startTime + timeout:
                raise AssertionError(
                    'Failed to receive all emails within %s seconds '
                    '(expected %s, received %s)' %
                    (timeout, count, count - remaining))

            time.sleep(0.1)
