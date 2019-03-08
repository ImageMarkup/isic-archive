import os

from setuptools import find_packages, setup

setup(
    name='isic-archive',
    version='1.0.0',
    description='The ISIC Archive API server.',
    url='https://github.com/ImageMarkup/isic-archive',

    packages=find_packages(),
    package_data={
        '': ['mail_templates/*.mako',
             'license_templates/*.mako',
             '*.mako'],
    },
    data_files=[(os.path.join('share', 'isic_archive'),
                 [os.path.join('isic-archive-gui', 'src', 'masterFeatures.json')])],
    install_requires=[
        'backports.csv',
        'celery[redis]',
        'geojson',
        'girder-large-image',
        'girder-gravatar',
        'girder-oauth',
        'girder>=3.0.0a2',
        'jsonpickle',
        'natsort',
        'numpy',
        'opencv-python',
        'pillow',
        'python-dateutil',
        'python-dotenv',
        'requests',
        'requests_toolbelt',
        'scikit-image',
        'scipy',
        'sentry-sdk',
        'six',
    ],
    entry_points={
        'girder.plugin': [
            'isic_archive = isic_archive:IsicArchive'
        ]
    }
)
