# coding=utf-8

from girder.utility.model_importer import ModelImporter


def getUDAuser():
    return ModelImporter.model('user').findOne({'login': 'udastudy'})


def getFoldersForCollection(collection, excludeFlagged=True):
    folder_query = ModelImporter.model('folder').find(
        {'parentId': collection['_id']})
    def filterFunc(folder):
        if collection['name'] == 'Phase 0' and folder['name'] in ['dropzip', 'dropcsv']:
            return False
        if excludeFlagged and folder['name'] == 'flagged':
            return False
        return True

    folders = filter(filterFunc, folder_query)
    return folders


def getItemsInFolder(folder):
    return list(ModelImporter.model('folder').childItems(folder, limit=0))


def getCollection(collectionName):
    return ModelImporter.model('collection').findOne({'name': collectionName})


def getFolder(collection, folderName):
    return ModelImporter.model('folder').findOne({
        'parentId': collection['_id'],
        'name': folderName
    })
