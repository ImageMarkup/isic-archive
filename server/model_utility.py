
from girder.utility.model_importer import ModelImporter
from girder.constants import TerminalColor, AccessType
from girder import events

import cherrypy
from bson.objectid import ObjectId, InvalidId
import json
import datetime
import stat
import tempfile, os
import mimetypes
from hashlib import sha512

def getUDAuser():
    m = ModelImporter()
    uda_user = getUser('udastudy')
    real_user = m.model('user').load(uda_user['_id'], force=True)
    return real_user


def getFoldersForCollection(collection, excludeFlagged=True):

    m = ModelImporter()
    folder_query = m.model('folder').find({'parentId': collection['_id']})
    folders = []
    if folder_query.count() > 0:
        for f in folder_query:
            if not (f['name'] == 'flagged' and excludeFlagged):
                folders.append(f)

    return folders



def getAssetStoreForItem(item):

    m = ModelImporter()

    files = m.model('item').childFiles(item, limit=1)

    firstFile = None
    for f in files:
        firstFile = f

    # print firstFile

    assetstore = m.model('assetstore').load(firstFile['assetstoreId'])

    return assetstore



def createFileObjectFromData(filename, item, assetstore, data, writeType='w'):

    m = ModelImporter()

    # load the asset store
    assetstore = m.model('assetstore').load(assetstore['_id'])

    # and a user that has write priviledges to the asset store (workaround)
    uda_user = getUser('udastudy')

    # get the temp directory
    tempDir = os.path.join(assetstore['root'], 'temp')

    # create a temp file there
    fd, tmppath = tempfile.mkstemp(dir=tempDir)

    # close it at the system levle (workaround)
    os.close(fd)

    # open it in python
    fout = open(tmppath, writeType)

    # read the file handle passed to this function
    buf = data

    # calculate file size
    newfileize = len(buf)

    # calculate sha512 checksum
    checksum = sha512()
    checksum.update(buf)

    # write it to the temp file
    fout.write(buf)

    # close target file
    fout.close()


    # generate the file names for storage in
    hash = checksum.hexdigest()
    dir = os.path.join(hash[0:2], hash[2:4])
    absdir = os.path.join(assetstore['root'], dir)

    path = os.path.join(dir, hash)
    abspath = os.path.join(assetstore['root'], path)

    if not os.path.exists(absdir):
        os.makedirs(absdir)

    if os.path.exists(abspath):
        # Already have this file stored, just delete temp file.
        print 'already exists, removing %s' % (tmppath)
        os.remove(tmppath)

    else:
        # Move the temp file to permanent location in the assetstore.
        print 'new file, moving and removing temp %s' % (tmppath)

        os.rename(tmppath, abspath)
        os.chmod(abspath, stat.S_IRUSR | stat.S_IWUSR)


    # guess its type
    guessed_mime = mimetypes.guess_type(filename)[0]

    # create
    new_file = m.model('file').createFile(uda_user, item, filename, newfileize, assetstore, guessed_mime)

    # update some params
    new_file['sha512'] = hash
    new_file['path'] = path
    new_file['size'] = newfileize

    # save it
    m.model('file').save(new_file)

    return new_file


    # returns the file item











def getItemsInFolder(folder):

    m = ModelImporter()
    item_query = m.model('item').find({'folderId': folder['_id']})
    items = []

    if item_query.count() > 0:

        for item in item_query:
            items.append(item)
    else:
        print 'no items in folder', folder['name']

    return items



def getWeightForGroup(groupName):

    # count number of images in phase 0 collection, not including flagged folder
    count = countImagesInCollection(groupName)
    weight = 0

    # assign a weight to phase
    if groupName == 'Phase 0':
        weight = 10
    elif groupName == 'Phase 1a':
        weight = 20
    elif groupName == 'Phase 1b':
        weight = 30
    elif groupName == 'Phase 1c':
        weight = 40
    elif groupName == 'Phase 1d':
        weight = 50
    elif groupName == 'Phase 2':
        weight = 60


    print 'weight for', groupName, weight, count
    return (count, weight)

def countImagesInCollection(collectionName):

    collection = getCollection(collectionName)

    folders = getFoldersForCollection(collection)

    total_len = 0

    for folder in folders:
        items = getItemsInFolder(folder)
        total_len += len(items)

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

