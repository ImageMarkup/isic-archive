from setuptools import find_packages, setup

setup(name='isic-archive-tasks',
      version='0.1',
      packages=find_packages(include=['isic_archive_tasks']),
      install_requires=[
          'celery[redis]',
          'jsonpickle',
          'python-dotenv',
          'requests',
          'requests_toolbelt',
          'sentry-sdk',
          'six'
      ])
