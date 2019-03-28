import pytest
from requests_toolbelt.sessions import BaseUrlSession

from isic_archive.models.dataset import Dataset


@pytest.fixture
def session():
    s = BaseUrlSession('http://girder:8080/api/v1/')
    r = s.get('user/authentication', auth=('admin', 'password'))
    r.raise_for_status()
    s.headers.update({'Girder-Token': r.json()['authToken']['token']})
    yield s


@pytest.fixture
def dataset_id(session):
    for dataset in Dataset().find():
        if dataset['name'] == 'test dataset':
            Dataset().remove(dataset)

    r = session.get('dataset', params={'limit': 1})
    r.raise_for_status()

    r = session.post(
        'dataset',
        data={
            'name': 'test dataset',
            'description': 'test dataset',
            'license': 'CC-BY',
            'attribution': 'test',
            'owner': 'test',
        },
    )
    r.raise_for_status()

    dataset_id = r.json()['_id']

    yield dataset_id

    dataset = Dataset().load(dataset_id, force=True)
    Dataset().remove(dataset)
