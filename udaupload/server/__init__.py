
from girder import events
from girder.constants import TerminalColor
from girder.utility.model_importer import ModelImporter

from pprint import pprint as pp
import zipfile
import mimetypes

from hashlib import sha512
import os
import tempfile
import stat


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



# zip file upload of packed images

def load(info):

    m = ModelImporter()

    # if uda study collection not present, create
    uda_user = m.model('user').find({'firstName' : 'uda'})

    uda_user = makeUserIfNotPresent('udastudy', 'udastudy', 'uda admin', 'testuser', 'admin@uda2study.org')
    uda_coll = makeCollectionIfNotPresent('UDA upload', uda_user, 'Upload folders')

    dropzipfolder = makeFolderIfNotPresent(uda_coll, 'dropzip', 'upload zip folder of images here', 'collection', False, uda_user)
    dropcsv = makeFolderIfNotPresent(uda_coll, 'dropcsv', 'upload image metadata as csv here', 'collection', False, uda_user)


def createFileInternal(assetstore, filehandle_to_read, file_name):
    '''

    :param assetstore:
    :param filehandle_to_read:
    :param file_name:
    :return:
    '''

    tempDir = os.path.join(assetstore['root'], 'temp')

    fd, tmppath = tempfile.mkstemp(dir=tempDir)
    ft, tmptiffpath = tempfile.mkstemp(dir=tempDir)

    os.close(ft)
    os.close(fd)

    tmppath += '.jpg'
    tmptiffpath += '.tif'

    # write jpeg from zip

    fout = open(tmppath, 'w')

    buf = filehandle_to_read.read()
    fout.write(buf)
    fout.close()
    filehandle_to_read.close()

    cmdstr = '/usr/local/bin/vips im_vips2tiff %s %s:jpeg:75,tile:256x256,pyramid,,,,8' % (tmppath, tmptiffpath)

    pipe = os.popen(cmdstr)
    for p in pipe:
        print p

    forCheck = open(tmptiffpath, 'r')
    hashBuf = forCheck.read()

    newfileize = len(hashBuf)

    checksum = sha512()
    checksum.update(hashBuf)

    forCheck.close()

    # vips im_vips2tiff %s %s:jpeg:75,tile:256x256,pyramid,,,,8

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
        os.remove(tmptiffpath)

    else:
        # Move the temp file to permanent location in the assetstore.
        print 'new file, moving and removing temp %s' % (tmptiffpath)

        os.remove(tmppath)
        os.rename(tmptiffpath, abspath)

        # make a .tif symlink
        tiffsymlink = abspath + '.tif'
        if os.path.exists(tiffsymlink):
            os.remove(tiffsymlink)

        os.symlink(abspath, tiffsymlink)

        os.chmod(abspath, stat.S_IRUSR | stat.S_IWUSR)

    return {
        'sha512' : hash,
        'path' : path,
        'size' : newfileize
    }



def uploadHandler(event):

    m = ModelImporter()

    pp(event.info)

    file_info = event.info['file']
    asset_store_info = event.info['assetstore']

    assetstore = m.model('assetstore').load(asset_store_info['_id'])

    item = m.model('item').load(file_info['itemId'], force=True)
    folder = m.model('folder').load(item['folderId'], force=True)

    uda_user = makeUserIfNotPresent('udastudy', 'udastudy', 'uda admin', 'testuser', 'admin@uda2study.org')
    uda_coll = makeCollectionIfNotPresent('UDA upload', uda_user, 'Upload folders')

    if folder['name'] == 'dropzip':

        if file_info['mimeType'] == 'application/zip':

            full_file_path = os.path.join(asset_store_info['root'], file_info['path'])

            zf = zipfile.ZipFile(open(full_file_path))
            base_file_name = file_info['name'].split('.')[0]
            print TerminalColor.info('Creating folder %s' % base_file_name)

            zipfolder = makeFolderIfNotPresent(uda_coll, base_file_name, '', 'collection', False, uda_user)

            for zfile in zf.infolist():

                guessed_mime = mimetypes.guess_type(zfile.filename)

                meta_dict = {}
                meta_dict['originalMimeType'] = guessed_mime[0]
                meta_dict['convertedMimeType'] = 'image/tiff'
                meta_dict['originalFilename'] = zfile.filename
                meta_dict['convertedFilename'] = zfile.filename.replace('.jpg', '.tif')

                z = zf.open(zfile)
                new_file_dict = createFileInternal(assetstore, z, zfile.filename)

                newitem = m.model('item').createItem(
                    name=meta_dict['convertedFilename'], creator=uda_user,
                    folder=zipfolder)

                newitem = m.model('item').setMetadata(newitem, metadata=meta_dict)

                file_entry= m.model('file').createFile(
                    item=newitem, name=meta_dict['convertedFilename'], size=new_file_dict['size'],
                    creator=uda_user, assetstore=assetstore,
                    mimeType=meta_dict['convertedMimeType'])

                file_entry['sha512'] = new_file_dict['sha512']
                file_entry['path'] = new_file_dict['path']

                m.model('file').save(file_entry)

        # not deleting original for archival purposes
        # m.model('item').remove(item)


    elif folder['name'] == 'dropcsv':

        if file_info['mimeType'] == 'text/csv':

            full_file_path = os.path.join(asset_store_info['root'], file_info['path'])

            import csv
            firstRow = True

            col_headers = []

            phase0_collection =  makeCollectionIfNotPresent('Phase 0', uda_user, 'Images to QC')
            phase0_images = makeFolderIfNotPresent(phase0_collection, 'images', '', 'collection', False, uda_user)


            with open(full_file_path, 'rU') as csvfile:
                csvread = csv.reader(csvfile, delimiter=',', quotechar='"')
                for row in csvread:

                    if firstRow:
                        col_headers = row
                        firstRow = False

                    else:

                        id_index = col_headers.index('isic_id')

                        possible_item = m.model('item').find({
                            'name' : row[id_index] + '.tif'
                        })

                        if possible_item.count() > 0:


                            new_metadata = dict(zip(col_headers, row))

                            item = possible_item[0]

                            print item

                            files = m.model('item').childFiles(item, limit=1)
                            firstFile = None
                            for f in files:
                                firstFile = f

                            print firstFile

                            assetstore = m.model('assetstore').load(firstFile['assetstoreId'])

                            newitem = m.model('item').createItem(
                                name=item['name'], creator=uda_user,
                                folder=phase0_images)

                            new_file= m.model('file').createFile(
                                item=newitem, name=item['meta']['convertedFilename'], size=firstFile['size'],
                                creator=uda_user, assetstore=assetstore,
                                mimeType=item['meta']['convertedMimeType'])

                            new_file['sha512'] = firstFile['sha512']
                            new_file['path'] = firstFile['path']

                            newitem = m.model('item').setMetadata(newitem, metadata=new_metadata)

                            m.model('file').save(new_file)
                            # addItemToPhase0(possible_item[0], new_metadata)



                            # m.model('item').setMetadata(possible_item[0], new_metadata)

        # not deleting original for archival purposes
        # m.model('item').remove(item)




events.bind('data.process', 'uploadHandler', uploadHandler)
