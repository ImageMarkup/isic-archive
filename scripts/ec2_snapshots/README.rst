EC2 Snapshots
=============
Utility to manage snapshots of volumes on an AWS EC2 instance
-------------------------------------------------------------

Prerequisites
~~~~~~~~~~~~~
* Install Python packages in ``requirements.txt``.

* Set up authentication credentials for `Boto 3`_; see documentation_.

Usage
~~~~~
* Display help:
  ::

    python ec2_snapshots.py --help

* Create snapshots:
  ::

    python ec2_snapshots.py create --instance-id <INSTANCE_ID>

* Clean snapshots:
  ::

    python ec2_snapshots.py clean --instance-id <INSTANCE_ID>


.. _Boto 3: http://boto3.readthedocs.io
.. _documentation: https://boto3.readthedocs.io/en/latest/guide/quickstart.html#configuration
