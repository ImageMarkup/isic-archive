from girder.utility import server as girder_server
girder_server.configureServer()
from girder.models.file import File  # noqa: E402, I100
from girder.models.folder import Folder  # noqa: E402
from girder.models.item import Item  # noqa: E402

from isic_archive.models.dataset import Dataset  # noqa: E402


for dataset in Dataset().find():
    print(dataset['name'])
    for registration in dataset['metadataFiles']:
        metadataFile = File().load(registration['fileId'], force=True)
        item = Item().load(metadataFile['itemId'], force=True)
        folder = Folder().load(item['folderId'], force=True)

        print(' ', metadataFile['name'])

        del metadataFile['itemId']
        metadataFile['attachedToType'] = ['dataset', 'isic_archive']
        metadataFile = File().save(metadataFile)

        File().propagateSizeChange(item, -metadataFile['size'])
        Item().remove(item)
        Folder().remove(folder)
