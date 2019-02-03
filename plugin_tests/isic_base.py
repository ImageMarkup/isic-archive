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

import time

from six.moves import queue

from tests import base


class IsicTestCase(base.TestCase):
    def setUp(self):
        # The isic_archive plugin provisions multiple magic collections, groups,
        # etc. upon startup. Under an upstream Girder testing workflow, the
        # server is started only once for the test module, then the database is
        # dropped before each test method. For isic_archive, this would cause
        # these magic database entries to be dropped and not regenerated. To
        # prevent this, we will drop the database and then re-provision the
        # database before each test method.
        # Attempting to restart the full server in between test methods is buggy
        # and fails.
        super(IsicTestCase, self).setUp()

        from girder.plugins.isic_archive.provision_utility import provisionDatabase

        provisionDatabase()

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
                    '(expected %s, received %s)' % (timeout, count, count - remaining)
                )

            time.sleep(0.1)
