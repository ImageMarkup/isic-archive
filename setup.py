from setuptools import find_packages, setup

setup(
    name='isic-archive',
    version='1.0.0',
    description='The ISIC Archive API server.',
    url='https://github.com/ImageMarkup/isic-archive',

    packages=find_packages(exclude=['plugin_tests']),
    package_data={
        '': ['mail_templates/*.mako'],
    },

    install_requires=[
        'backports.csv>=1.0.5',
        'celery[redis]',
        'geojson>=1.3.2',
        'girder-large-image',
        'girder-oauth',
        'girder>=3.0.0a2',
        'jsonpickle',
        'natsort>=5.0.0',
        'numpy>=1.10.2',
        'opencv-python>=4',
        'pillow',
        'python-dateutil',
        'python-dotenv',
        'python-dotenv',
        'requests',
        'requests_toolbelt',
        'scikit-image>=0.12.3',
        'scipy>=0.16.0',
        'sentry-sdk',
        'six',
    ],
    extras_require={
        'dev': [
            'tox'
        ]
    },
    dependency_links=[
        'https://github.com/ImageMarkup/isic-archive/tarball/master#egg=girder'
    ],
    entry_points={
        'girder.plugin': [
            'isic_archive = isic_archive:IsicArchive'
        ]
    }
)
