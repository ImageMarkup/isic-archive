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
Utility to mirror volumes across AWS EC2 instances.

Currently ignores the root volume, because according to the documentation [1]
the instance should be stopped before creating a snapshot of the root volume.

[1] http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ebs-creating-snapshot.html
"""

import datetime
import logging

import boto3
import click
import six


def _getNameTagValue(obj):
    """
    Given an object with a 'tags' attribute, get the value of the tag with key 'Name'.

    Tags are in format: [{'Key': 'string','Value': 'string'}, ...].
    """
    if not hasattr(obj, 'tags') or obj.tags is None:
        return None
    name = [tag['Value']
            for tag in obj.tags
            if tag['Key'] == 'Name']
    return name[0] if name else None


@click.group()
def main():
    pass


@main.command()
@click.option('--from-instance-id', required=True, help='Source AWS EC2 Instance ID')
@click.option('--to-instance-id', required=True, help='Destination AWS EC2 Instance ID')
@click.option('--dry-run', default=False, is_flag=True,
              help='Log actions without performing them')
def mirror(from_instance_id, to_instance_id, dry_run):
    """Create snapshots of all volumes of an instance except the root volume."""
    ec2 = boto3.resource('ec2')
    ec2Client = boto3.client('ec2')

    fromInstance = ec2.Instance(id=from_instance_id)
    toInstance = ec2.Instance(id=to_instance_id)
    logging.info('Mirroring non-root volumes from %s to %s', fromInstance, toInstance)

    fromVolumesByMapping = {
        mapping['DeviceName']: ec2.Volume(mapping['Ebs']['VolumeId'])
        for mapping in fromInstance.block_device_mappings
    }
    oldToVolumesByMapping = {
        mapping['DeviceName']: ec2.Volume(mapping['Ebs']['VolumeId'])
        for mapping in toInstance.block_device_mappings
    }
    # Exclude the root volume
    del fromVolumesByMapping[fromInstance.root_device_name]

    logging.info('Stopping destination instance %s', toInstance)
    toInstance.stop()
    toInstance.wait_until_stopped()
    logging.info('Stopped destination instance %s', toInstance)

    for mapping, fromVolume in six.viewitems(fromVolumesByMapping):
        oldToVolume = oldToVolumesByMapping[mapping]
        logging.info('Mirroring volume %s, overwriting %s', fromVolume, oldToVolume)

        fromVolumeName = _getNameTagValue(fromVolume)
        now = datetime.datetime.utcnow()
        snapshotDescription = '%s:%s' % (
            fromVolumeName, now.replace(microsecond=0, tzinfo=None).isoformat())
        if dry_run:
            continue

        logging.info('Creating snapshot (named %s)', snapshotDescription)
        snapshot = fromVolume.create_snapshot(
            Description=snapshotDescription,
        )
        logging.info('Started snapshot %s (%s)', snapshot.id, snapshotDescription)
        logging.info('Started snapshot %s', snapshot)
        snapshot.create_tags(
            Tags=[
                {
                    'Key': 'Name',
                    'Value': snapshotDescription
                }
            ]
        )
        snapshot.wait_until_completed()
        logging.info('Snapshot completed %s', snapshot)

        toVolumeName = _getNameTagValue(oldToVolume)
        logging.info('Creating new volume (named %s)', toVolumeName)
        newToVolume = ec2.create_volume(
            AvailabilityZone=oldToVolume.availability_zone,
            SnapshotId=snapshot.id,
            VolumeType='gp2',
            TagSpecifications=[
                {
                    'ResourceType': 'volume',
                    'Tags': [
                        {
                            'Key': 'Name',
                            'Value': toVolumeName
                        }
                    ]
                }
            ]
        )
        ec2Client.get_waiter('volume_available').wait(
            VolumeIds=[newToVolume.id]
        )
        logging.info('Created new volume %s', newToVolume)

        logging.info('Deleting snapshot %s', snapshot)
        snapshot.delete()

        logging.info('Detaching old volume %s', oldToVolume)
        oldToVolume.detach_from_instance()
        ec2Client.get_waiter('volume_available').wait(
            VolumeIds=[oldToVolume.id]
        )
        logging.info('Detached old volume %s', oldToVolume)

        logging.info('Attaching new volume %s to instance %s at %r',
                     newToVolume, toInstance, mapping)
        newToVolume.attach_to_instance(
            Device=mapping,
            InstanceId=toInstance.id
        )
        ec2Client.get_waiter('volume_in_use').wait(
            VolumeIds=[newToVolume.id]
        )
        logging.info('Attached new volume %s', oldToVolume)

        logging.info('Deleting old volume %s', oldToVolume)
        oldToVolume.delete()

    logging.info('Starting destination instance %s', toInstance)
    toInstance.start()
    toInstance.wait_until_running()
    logging.info('Started destination instance %s', toInstance)

    logging.info('Done')


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main()
