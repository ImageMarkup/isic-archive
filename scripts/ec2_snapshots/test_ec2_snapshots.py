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

import unittest

import dateutil
import mock

from ec2_snapshots import getRetainedDaily, getRetainedMonthly, getRetainedWeekly, getRetainedYearly


class EC2SnapshotsTestCase(unittest.TestCase):
    def setUp(self):
        # Create a list of assorted mock snapshots sorted by start_time.
        self.snapshots = sorted([
            self._createSnapshot('2011-02-12 18:30:00+00:00'),
            self._createSnapshot('2013-01-12 18:30:00+00:00'),
            self._createSnapshot('2014-02-04 11:59:30+00:00'),
            self._createSnapshot('2014-08-04 11:59:30+00:00'),
            self._createSnapshot('2015-01-12 18:30:00+00:00'),
            self._createSnapshot('2016-01-12 18:30:00+00:00'),
            self._createSnapshot('2016-03-22 18:30:00+00:00'),
            self._createSnapshot('2016-12-01 18:30:00+00:00'),
            self._createSnapshot('2016-12-03 18:30:00+00:00'),
            self._createSnapshot('2017-01-12 18:30:00+00:00'),
            self._createSnapshot('2017-01-14 18:30:00+00:00'),
            self._createSnapshot('2017-02-01 18:30:00+00:00'),
            self._createSnapshot('2017-04-15 18:30:00+00:00'),
            self._createSnapshot('2017-04-16 18:30:00+00:00'),
            self._createSnapshot('2017-04-17 18:30:00+00:00'),
            self._createSnapshot('2017-08-04 11:59:30+00:00'),
            self._createSnapshot('2017-08-14 18:30:00+00:00')
        ], key=lambda s: s.start_time)

    def _getSnapshot(self, date):
        date = self._createDatetime(date)
        return next((snapshot for snapshot in self.snapshots if snapshot.start_time == date), None)

    def _createDatetime(self, date):
        """Convert datetime objects or ISO 8601-formatted strings to datetime objects in UTC."""
        date = str(date).strip()
        try:
            date = dateutil.parser.parse(date)
            if date.tzinfo is None:
                date = date.replace(tzinfo=dateutil.tz.tzutc())
        except ValueError:
            raise Exception('Invalid date format.')

        return date

    def _createSnapshot(self, start_time):
        """Create a mock EC2.Snapshot instance that has a start_date attribute."""
        snapshot = mock.NonCallableMock()
        snapshot.start_time = self._createDatetime(start_time)
        return snapshot

    def test_retainedYearly(self):
        now = self._createDatetime('2017-06-01')
        retained = getRetainedYearly(6, now, self.snapshots)
        self.assertEqual(5, len(retained))
        self.assertIn(self._getSnapshot('2011-02-12 18:30:00+00:00'), retained)
        self.assertIn(self._getSnapshot('2013-01-12 18:30:00+00:00'), retained)
        self.assertIn(self._getSnapshot('2014-08-04 11:59:30+00:00'), retained)
        self.assertIn(self._getSnapshot('2015-01-12 18:30:00+00:00'), retained)
        self.assertIn(self._getSnapshot('2016-12-03 18:30:00+00:00'), retained)
        retained = getRetainedYearly(5, now, self.snapshots)
        self.assertEqual(4, len(retained))
        self.assertIn(self._getSnapshot('2013-01-12 18:30:00+00:00'), retained)
        self.assertIn(self._getSnapshot('2014-08-04 11:59:30+00:00'), retained)
        self.assertIn(self._getSnapshot('2015-01-12 18:30:00+00:00'), retained)
        self.assertIn(self._getSnapshot('2016-12-03 18:30:00+00:00'), retained)
        retained = getRetainedYearly(4, now, self.snapshots)
        self.assertEqual(4, len(retained))
        self.assertIn(self._getSnapshot('2013-01-12 18:30:00+00:00'), retained)
        self.assertIn(self._getSnapshot('2014-08-04 11:59:30+00:00'), retained)
        self.assertIn(self._getSnapshot('2015-01-12 18:30:00+00:00'), retained)
        self.assertIn(self._getSnapshot('2016-12-03 18:30:00+00:00'), retained)
        retained = getRetainedYearly(3, now, self.snapshots)
        self.assertEqual(3, len(retained))
        self.assertIn(self._getSnapshot('2014-08-04 11:59:30+00:00'), retained)
        self.assertIn(self._getSnapshot('2015-01-12 18:30:00+00:00'), retained)
        self.assertIn(self._getSnapshot('2016-12-03 18:30:00+00:00'), retained)
        retained = getRetainedYearly(2, now, self.snapshots)
        self.assertEqual(2, len(retained))
        self.assertIn(self._getSnapshot('2015-01-12 18:30:00+00:00'), retained)
        self.assertIn(self._getSnapshot('2016-12-03 18:30:00+00:00'), retained)
        retained = getRetainedYearly(1, now, self.snapshots)
        self.assertEqual(1, len(retained))
        self.assertIn(self._getSnapshot('2016-12-03 18:30:00+00:00'), retained)
        retained = getRetainedYearly(0, now, self.snapshots)
        self.assertEqual(0, len(retained))
        retained = getRetainedYearly(-1, now, self.snapshots)
        self.assertEqual(0, len(retained))

    def test_retainedMonthly(self):
        now = self._createDatetime('2017-06-01')
        retained = getRetainedMonthly(6, now, self.snapshots)
        self.assertEqual(4, len(retained))
        self.assertIn(self._getSnapshot('2016-12-03 18:30:00+00:00'), retained)
        self.assertIn(self._getSnapshot('2017-01-14 18:30:00+00:00'), retained)
        self.assertIn(self._getSnapshot('2017-02-01 18:30:00+00:00'), retained)
        self.assertIn(self._getSnapshot('2017-04-17 18:30:00+00:00'), retained)
        retained = getRetainedMonthly(5, now, self.snapshots)
        self.assertEqual(3, len(retained))
        self.assertIn(self._getSnapshot('2017-01-14 18:30:00+00:00'), retained)
        self.assertIn(self._getSnapshot('2017-02-01 18:30:00+00:00'), retained)
        self.assertIn(self._getSnapshot('2017-04-17 18:30:00+00:00'), retained)
        retained = getRetainedMonthly(4, now, self.snapshots)
        self.assertEqual(2, len(retained))
        self.assertIn(self._getSnapshot('2017-02-01 18:30:00+00:00'), retained)
        self.assertIn(self._getSnapshot('2017-04-17 18:30:00+00:00'), retained)

        now = self._createDatetime('2017-01-01')
        retained = getRetainedMonthly(12, now, self.snapshots)
        self.assertEqual(3, len(retained))
        self.assertIn(self._getSnapshot('2016-01-12 18:30:00+00:00'), retained)
        self.assertIn(self._getSnapshot('2016-03-22 18:30:00+00:00'), retained)
        self.assertIn(self._getSnapshot('2016-12-03 18:30:00+00:00'), retained)

    def test_retainedWeekly(self):
        now = self._createDatetime('2017-08-16')  # Wednesday
        retained = getRetainedWeekly(1, now, self.snapshots)
        self.assertEqual(1, len(retained))
        self.assertIn(self._getSnapshot('2017-08-14 18:30:00+00:00'), retained)
        retained = getRetainedWeekly(2, now, self.snapshots)
        self.assertEqual(1, len(retained))
        self.assertIn(self._getSnapshot('2017-08-14 18:30:00+00:00'), retained)
        retained = getRetainedWeekly(3, now, self.snapshots)
        self.assertEqual(2, len(retained))
        self.assertIn(self._getSnapshot('2017-08-04 11:59:30+00:00'), retained)
        self.assertIn(self._getSnapshot('2017-08-14 18:30:00+00:00'), retained)

        now = self._createDatetime('2017-01-14')  # Saturday
        retained = getRetainedWeekly(1, now, self.snapshots)
        self.assertEqual(1, len(retained))
        self.assertIn(self._getSnapshot('2017-01-14 18:30:00+00:00'), retained)
        retained = getRetainedWeekly(2, now, self.snapshots)
        self.assertEqual(1, len(retained))
        self.assertIn(self._getSnapshot('2017-01-14 18:30:00+00:00'), retained)
        retained = getRetainedWeekly(7, now, self.snapshots)
        self.assertEqual(2, len(retained))
        self.assertIn(self._getSnapshot('2016-12-03 18:30:00+00:00'), retained)
        self.assertIn(self._getSnapshot('2017-01-14 18:30:00+00:00'), retained)

    def test_retainedDaily(self):
        now = self._createDatetime('2017-08-16')
        retained = getRetainedDaily(1, now, self.snapshots)
        self.assertEqual(0, len(retained))
        retained = getRetainedDaily(2, now, self.snapshots)
        self.assertEqual(0, len(retained))
        retained = getRetainedDaily(3, now, self.snapshots)
        self.assertEqual(1, len(retained))
        self.assertIn(self._getSnapshot('2017-08-14 18:30:00+00:00'), retained)

        now = self._createDatetime('2017-08-14')
        retained = getRetainedDaily(5, now, self.snapshots)
        self.assertEqual(1, len(retained))
        self.assertIn(self._getSnapshot('2017-08-14 18:30:00+00:00'), retained)
        retained = getRetainedDaily(11, now, self.snapshots)
        self.assertEqual(2, len(retained))
        self.assertIn(self._getSnapshot('2017-08-04 11:59:30+00:00'), retained)
        self.assertIn(self._getSnapshot('2017-08-14 18:30:00+00:00'), retained)

        now = self._createDatetime('2017-04-17')
        retained = getRetainedDaily(1, now, self.snapshots)
        self.assertEqual(1, len(retained))
        self.assertIn(self._getSnapshot('2017-04-17 18:30:00+00:00'), retained)
        retained = getRetainedDaily(2, now, self.snapshots)
        self.assertEqual(2, len(retained))
        self.assertIn(self._getSnapshot('2017-04-16 18:30:00+00:00'), retained)
        self.assertIn(self._getSnapshot('2017-04-17 18:30:00+00:00'), retained)
        retained = getRetainedDaily(3, now, self.snapshots)
        self.assertEqual(3, len(retained))
        self.assertIn(self._getSnapshot('2017-04-15 18:30:00+00:00'), retained)
        self.assertIn(self._getSnapshot('2017-04-16 18:30:00+00:00'), retained)
        self.assertIn(self._getSnapshot('2017-04-17 18:30:00+00:00'), retained)

    if __name__ == '__main__':
        unittest.main()
