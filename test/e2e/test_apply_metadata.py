from girder.models.user import User

from isic_archive.models.dataset import Dataset
from isic_archive.models.image import Image


def test_apply_metadata(session, dataset_id):
    user = list(User().getAdmins())[0]
    dataset = Dataset().load(dataset_id, force=True)
    image = Dataset().addImage(
        dataset, open('test/data/should-pass.jpg', 'rb'), 286_460, 'foo.jpg', 'some-signature', user
    )
    with open('test/data/test-metadata.csv') as infile:
        r = session.post(
            f'dataset/{dataset_id}/metadata',
            params={'filename': 'test-metadata.csv'},
            data=infile.read(),
            headers={'Content-Type': 'text/csv'},
        )
        r.raise_for_status()

    # reload to capture metadata file id
    dataset = Dataset().load(dataset_id, force=True)
    metadata_file_id = dataset['metadataFiles'][-1]['fileId']
    r = session.post(f'dataset/{dataset_id}/metadata/{metadata_file_id}/apply', data={'save': True})
    assert r.ok, r.text
    image = Image().load(image['_id'], force=True)
    assert image['meta']['clinical']['benign_malignant'] == 'benign'
    assert image['meta']['unstructured']['some_key'] == 'some_value'
