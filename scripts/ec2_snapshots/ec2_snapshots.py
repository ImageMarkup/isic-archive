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

"""
Utility to manage snapshots of volumes on an AWS EC2 instance.

Currently ignores the root volume, because according to the documentation [1]
the instance should be stopped before creating a snapshot of the root volume.

[1] http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ebs-creating-snapshot.html
"""

import boto3
import click
import datetime
import dateutil
import functools
import logging

from dateutil.relativedelta import relativedelta, SU


def _getInstance(instance_id):
    """
    Get the EC2 instance.
    """
    ec2 = boto3.resource('ec2')

    # Get EC2 instance
    instance = list(ec2.instances.filter(
        InstanceIds=[instance_id]
    ))
    if not instance:
        raise Exception('Instance not found')
    instance = instance[0]
    logging.info('Found instance: %s', instance)
    logging.info('Instance root: %s', instance.root_device_name)
    return instance


def _getRootVolumeId(instance):
    """
    Get the ID of the root volume on the given instance.
    """
    rootVolumeId = [mapping['Ebs']['VolumeId']
                    for mapping in instance.block_device_mappings
                    if mapping['DeviceName'] == instance.root_device_name]
    if not rootVolumeId:
        raise Exception('Unable to identify root volume')

    rootVolumeId = rootVolumeId[0]
    logging.info('Root Volume Id: %s', rootVolumeId)

    return rootVolumeId


def _getNameTagValue(obj):
    """
    Given an object with a 'tags' attribute, get the value of the tag with key 'Name'. Tags are
    in format: [{'Key': 'string','Value': 'string'}, ...].
    """
    if not hasattr(obj, 'tags') or obj.tags is None:
        return None
    name = [tag['Value']
            for tag in obj.tags
            if tag['Key'] == 'Name']
    return name[0] if name else None


def _common_options(func):
    """
    Function that can be used as a decorator to add common options to commands.
    """
    @click.option('--instance-id', required=True, help='AWS EC2 Instance ID')
    @click.option('--dry-run', default=False, is_flag=True,
                  help='Log actions without performing them')
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper


@click.group()
def main():
    pass


@main.command()
@_common_options
def create(instance_id, dry_run):
    """
    Create snapshots of all volumes of an instance except the root volume.
    """
    instance = _getInstance(instance_id)
    rootVolumeId = _getRootVolumeId(instance)

    # Create snapshots of all volumes except root volume
    volumes = instance.volumes.all()
    for volume in volumes:
        volumeName = _getNameTagValue(volume)
        logging.info('Found volume: %s (%s)', volume.id, volumeName)
        if volume.id == rootVolumeId:
            logging.info('  skipping root volume %s', rootVolumeId)
            continue

        now = datetime.datetime.utcnow()
        description = '%s:%s' % (volumeName, now.replace(microsecond=0, tzinfo=None).isoformat())
        if dry_run:
            logging.info('Would create snapshot with description: %s', description)
            continue
        snapshot = volume.create_snapshot(
            Description=description,
        )
        logging.info('Created snapshot: %s (%s)', snapshot.id, description)
        snapshot.create_tags(
            Tags=[
                {
                    'Key': 'Name',
                    'Value': description
                }
            ]
        )


@main.command()
@_common_options
def clean(instance_id, dry_run):
    """
    Clean snapshots of all volumes of an instance except the root volume according to
    a hard-coded retention policy:
    - Keep daily snapshots for five days.
    - Keep weekly snapshots for two weeks.
    - Keep monthly snapshots for six months.
    - Keep yearly snapshots for one year.

    See the individual functions for how each type of snapshot is determined.

    Retention policy is based on description here:
    https://campus.barracuda.com/product/backup/article/BBS/RetentionPolicyEx/.
    """
    instance = _getInstance(instance_id)
    rootVolumeId = _getRootVolumeId(instance)

    now = datetime.datetime.utcnow().replace(tzinfo=dateutil.tz.tzutc())

    # Get volumes available on instance
    volumes = instance.volumes.all()
    for volume in volumes:
        volumeName = _getNameTagValue(volume)
        logging.info('Found volume: %s (%s)', volume.id, volumeName)
        if volume.id == rootVolumeId:
            logging.info('  skipping root volume %s', rootVolumeId)
            continue

        snapshots = volume.snapshots.all()

        # Select snapshots to retain
        retainedSnapshots = set()
        retainedSnapshots.update(getRetainedYearly(years=1, now=now, snapshots=snapshots))
        retainedSnapshots.update(getRetainedMonthly(months=6, now=now, snapshots=snapshots))
        retainedSnapshots.update(getRetainedWeekly(weeks=2, now=now, snapshots=snapshots))
        retainedSnapshots.update(getRetainedDaily(days=5, now=now, snapshots=snapshots))

        # Delete snapshots that aren't selected to retain
        toDelete = set(snapshots) - retainedSnapshots
        numSnapshots = (len(toDelete) + len(retainedSnapshots))
        logging.info('Deleting %d of %d snapshot(s) for volume %s', len(toDelete), numSnapshots,
                     volume.id)
        for snapshot in toDelete:
            if dry_run:
                logging.info('Would delete snapshot: %s (%s)', snapshot.id, snapshot.description)
                continue
            snapshot.delete()
            logging.info('Deleted snapshot %s (%s)', snapshot.id, snapshot.description)


def _getLastSnapshot(snapshots, start, end):
    """
    Get the last snapshot in the given date range.
    :param snapshots: Candidate snapshots
    :type snapshots: iterable of EC2.Snapshot
    :param start: start of date range
    :type start: datetime
    :param end: end of date range
    :type end: datetime
    :return: The last snapshot in the given date range
    """
    candidates = [snapshot for snapshot in snapshots if start <= snapshot.start_time < end]
    if not candidates:
        return None
    return max(candidates, key=lambda candidate: candidate.start_time)


def getRetainedYearly(years, now, snapshots):
    """
    Get snapshots to retain as yearly snapshots.
    A yearly snapshot is the last snapshot in a given calendar year.
    :param years: The number of years for which to retain snapshots
    :type years: int
    :param now: The current date/time
    :type now: datetime
    :param snapshots: Candidate snapshots
    :type snapshots: iterable of EC2.Snapshot
    """
    retained = set()
    for year in range(years):
        start = now.replace(now.year, 1, 1, 0, 0, 0, 0) + relativedelta(years=-(year+1))
        end = start + relativedelta(years=1)
        snapshot = _getLastSnapshot(snapshots, start, end)
        if snapshot:
            retained.add(snapshot)
    return retained


def getRetainedMonthly(months, now, snapshots):
    """
    Get snapshots to retain as monthly snapshots.
    A monthly snapshot is the last snapshot in a given calendar month.
    :param months: The number of months for which to retain snapshots
    :type months: int
    :param now: The current date/time
    :type now: datetime
    :param snapshots: Candidate snapshots
    :type snapshots: iterable of EC2.Snapshot
    """
    retained = set()
    for month in range(months):
        start = now.replace(now.year, now.month, 1, 0, 0, 0, 0) + relativedelta(months=-(month+1))
        end = start + relativedelta(months=1)
        snapshot = _getLastSnapshot(snapshots, start, end)
        if snapshot:
            retained.add(snapshot)
    return retained


def getRetainedWeekly(weeks, now, snapshots):
    """
    Get snapshots to retain as weekly snapshots.
    A weekly snapshot is the last snapshot on Sunday.
    :param weeks: The number of weeks for which to retain snapshots
    :type weeks: int
    :param now: The current date/time
    :type now: datetime
    :param snapshots: Candidate snapshots
    :type snapshots: iterable of EC2.Snapshot
    """
    retained = set()
    for week in range(weeks):
        # Start at most recent Sunday
        start = now.replace(now.year, now.month, now.day, 0, 0, 0, 0) +\
            relativedelta(weekday=SU(-1), weeks=-week)
        end = start + relativedelta(weeks=1)
        snapshot = _getLastSnapshot(snapshots, start, end)
        if snapshot:
            retained.add(snapshot)
    return retained


def getRetainedDaily(days, now, snapshots):
    """
    Get snapshots to retain as daily snapshots.
    A daily snapshot is the last snapshot on a given day.
    :param days: The number of days for which to retain snapshots
    :type days: int
    :param now: The current date/time
    :type now: datetime
    :param snapshots: Candidate snapshots
    :type snapshots: iterable of EC2.Snapshot
    """
    retained = set()
    for day in range(days):
        start = now.replace(now.year, now.month, now.day, 0, 0, 0, 0) + relativedelta(days=-day)
        end = start + relativedelta(days=1)
        snapshot = _getLastSnapshot(snapshots, start, end)
        if snapshot:
            retained.add(snapshot)
    return retained


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main()
