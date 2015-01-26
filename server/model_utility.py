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



def makeUserIfNotPresent(username, password, firstName, lastName, email):

    m = ModelImporter()

    user_query = m.model('user').find({'firstName' : firstName})

    user = None

    if user_query.count() == 0:
        # user doens't exist, create
        user = m.model('user').createUser(username, password, firstName, lastName, email)

    elif user_query.count() == 1:
        user = user_query[0]

    else:
        print TerminalColor.error('More than one user with same first name, returning first')
        user = user_query[0]

    return user



def makeFolderIfNotPresent(collection, folderName, folderDescription, parentType, public, creator):


    m = ModelImporter()

    folder_query = m.model('folder').find(
        { '$and' : [
            {'parentId': collection['_id']},
            {'name': folderName}
        ]})

    folder = None

    if folder_query.count() == 0:
        folder = m.model('folder').createFolder(collection, folderName, folderDescription, parentType=parentType, public=public, creator=creator)

    else:
        folder = folder_query[0]



    return folder




def makeGroupIfNotPresent(groupName, creator, description):

    m = ModelImporter()

    group_query = m.model('group').find({'name' : groupName})
    group = None

    if group_query.count() == 0:
        group = m.model('group').createGroup(groupName, creator, description)

    elif group_query.count() == 1:
        group = group_query[0]

    else:
        print TerminalColor.error('More than one group with this name, returning first')
        group = group_query[0]

    return group


def makeCollectionIfNotPresent(collectionName, creator, description):

    m = ModelImporter()

    collection_query = m.model('collection').find({'name' : collectionName})
    collection = None

    if collection_query.count() == 0:
        collection = m.model('collection').createCollection(collectionName, creator, description, public=False)

    elif collection_query.count() == 1:
        collection = collection_query[0]

    else:
        print TerminalColor.error('More than one collection with this name, returning first')
        collection = collection_query[0]

    return collection

