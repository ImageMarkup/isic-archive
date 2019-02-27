from setuptools import find_packages, setup

setup(
    name='isic-archive',
    version='1.0.0',
    description='The ISIC Archive API server.',
    url='https://github.com/ImageMarkup/isic-archive',

    packages=find_packages(
        exclude=['plugin_tests']
    ),
    package_data={
        '': ['mail_templates/*.mako'],
    },

    install_requires=[
        'girder>=3.0.0a2',
        'girder-oauth',
        'girder-large-image',
        'backports.csv>=1.0.5',
        'geojson>=1.3.2',
        'python-dateutil',
        'natsort>=5.0.0',
        'numpy>=1.10.2',
        'Pillow',
        'scipy>=0.16.0',
        'scikit-image>=0.12.3',
        'opencv-python>=4',
        'python-dotenv',
        'sentry-sdk'
    ],
    dependency_links=[
        'https://github.com/ImageMarkup/isic-archive/tarball/master#egg=girder'
    ],
    entry_points={
        'girder.plugin': [
            'isic_archive = isic_archive:IsicArchive'
        ]
    }
)
