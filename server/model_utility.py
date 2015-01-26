# coding=utf-8

from girder.utility.model_importer import ModelImporter


def getUDAuser():
    m = ModelImporter()
    uda_user = getUser('udastudy')
    real_user = m.model('user').load(uda_user['_id'], force=True)
    return real_user


def getFoldersForCollection(collection, excludeFlagged=True):
    m = ModelImporter()

    folder_query = m.model('folder').find({'parentId': collection['_id']})
    def filterFunc(folder):
        if collection['name'] == 'Phase 0' and folder['name'] in ['dropzip', 'dropcsv']:
            return False
        if excludeFlagged and folder['name'] == 'flagged':
            return False
        return True

    folders = filter(filterFunc, folder_query)
    return folders


def getItemsInFolder(folder):
    m = ModelImporter()
    return list(m.model('folder').childItems(folder, limit=0))


def countImagesInCollection(collectionName):
    collection = getCollection(collectionName)
    total_len = sum(len(getItemsInFolder(folder)) for folder in getFoldersForCollection(collection))
    return total_len


def getCollection(collectionName):

    m = ModelImporter()

    collection_query = m.model('collection').find({'name' : collectionName})
    collection = None

    if collection_query.count() != 0:
        collection = collection_query[0]
    else:
        print 'no collection found'

    return collection


def getUser(login):

    m = ModelImporter()

    user_query = m.model('user').find({'login' : login})
    user = None

    if user_query.count() == 1:
        user = user_query[0]
    else:
        print 'no user found'

    return user


def getFolder(collection, folderName):

    m = ModelImporter()
    folder_query = m.model('folder').find(
        { '$and' : [
            {'parentId': collection['_id']},
            {'name': folderName}
        ]})

    print folder_query.count()

    folder = None
    if folder_query.count() != 0:
        folder = folder_query[0]
    else:
        print 'no folder found'

    return folder
