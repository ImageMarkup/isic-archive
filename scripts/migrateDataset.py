from girder.utility import server as girder_server
girder_server.configureServer()

from girder.models.collection import Collection  # noqa: E402
from girder.models.folder import Folder  # noqa: E402
from girder.plugins.isic_archive.models.batch import Batch  # noqa: E402
from girder.plugins.isic_archive.models.dataset import Dataset  # noqa: E402
from girder.plugins.isic_archive.models.image import Image  # noqa: E402

for datasetFolder in Folder().find({
    'parentId': Collection().findOne({'name': 'Lesion Images'},)['_id']
}):
    dataset = Dataset().save({
        # Public informational data
        'name': datasetFolder['name'],
        'description': datasetFolder['description'],
        'license': datasetFolder['meta']['license'],
        'attribution':
            datasetFolder['meta']['attribution']
            if not datasetFolder['meta']['anonymous'] else
            'Anonymous',
        # Public Girder data
        'created': datasetFolder['created'],
        'updated': datasetFolder['updated'],
        # Private informational data
        'owner': datasetFolder['meta']['owner'],
        'metadataFiles': datasetFolder['meta']['metadataFiles'],
        # Private Girder data
        'creatorId': datasetFolder['creatorId'],
        'folderId': datasetFolder['_id'],
        'public': datasetFolder['public'],
        'access': datasetFolder['access']
    })

    # Propagate correct accesses to folder
    Dataset().setAccessList(dataset, dataset['access'])
    datasetFolder = Folder().load(datasetFolder['_id'], force=True)

    batch = Batch().save({
        'datasetId': dataset['_id'],
        'created': dataset['created'],
        'creatorId': dataset['creatorId'],
        'signature': datasetFolder['meta']['signature']
    })

    datasetFolder['meta'] = {}
    Folder().save(datasetFolder)


for image in Image().find():
    dataset = Dataset().findOne({'folderId': image['folderId']})
    # Right now, there will be only one batch per dataset
    batch = Batch().findOne({'datasetId': dataset['_id']})

    image['meta']['datasetId'] = dataset['_id']
    image['meta']['batchId'] = batch['_id']

    Image().save(image)
