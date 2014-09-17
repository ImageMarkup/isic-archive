__author__ = 'stonerri'



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

from model_utility import *



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

    print tmptiffpath
    print tmppath

    fout = open(tmppath, 'w')

    buf = filehandle_to_read.read()
    fout.write(buf)
    fout.close()
    filehandle_to_read.close()

    cmdstr = '/usr/local/bin/vips im_vips2tiff %s %s:jpeg:75,tile:256x256,pyramid,,,,8' % (tmppath, tmptiffpath)
    print cmdstr
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

    file_creator = m.model('user').load(item['creatorId'], force=True)

    uda_user = getUser('udastudy')
    phase0_collection = getCollection('Phase 0')


    if folder['name'] == 'dropzip':

        possible_zip_formats = ['application/octet-stream','multipart/x-zip','application/zip','application/zip-compressed','application/x-zip-compressed']

        if file_info['mimeType'] in possible_zip_formats:

            full_file_path = os.path.join(asset_store_info['root'], file_info['path'])

            zf = zipfile.ZipFile(open(full_file_path))
            base_file_name = file_info['name'].split('.')[0]

            print TerminalColor.info('Creating folder %s' % base_file_name)

            # create the folder as udaadmin
            zipfolder = makeFolderIfNotPresent(phase0_collection, base_file_name, '', 'collection', False, uda_user)

            # give the file uploader admin access
            m.model('folder').setUserAccess(zipfolder, file_creator, AccessType.ADMIN, save=True)

            print zf.infolist()

            for zfile in zf.infolist():

                print zfile.filename

                guessed_mime = mimetypes.guess_type(zfile.filename)

                print '### guessed_mime', guessed_mime

                meta_dict = {}
                meta_dict['originalMimeType'] = guessed_mime[0]
                meta_dict['convertedMimeType'] = 'image/tiff'
                meta_dict['originalFilename'] = zfile.filename
                meta_dict['convertedFilename'] = zfile.filename.replace('.jpg', '.tif')

                z = zf.open(zfile)
                new_file_dict = createFileInternal(assetstore, z, zfile.filename)

                newitem = m.model('item').createItem(
                    name=meta_dict['convertedFilename'], creator=file_creator,
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

            with open(full_file_path, 'rU') as csvfile:
                csvread = csv.reader(csvfile, delimiter=',', quotechar='"')
                for row in csvread:

                    # populate headers
                    if firstRow:
                        col_headers = row
                        firstRow = False

                    # get each image stored as a csv
                    else:

                        id_index = col_headers.index('isic_id')
                        possible_item = m.model('item').find({
                            'name' : row[id_index] + '.tif'
                        })

                        if possible_item.count() > 0:

                            full_metadata = dict(zip(col_headers, row))

                            new_metadata = dict((k, v) for k, v in full_metadata.iteritems() if v)

                            item = possible_item[0]

                            # todo: decide if we need to move when we map via csv
                            move_item = False

                            if move_item:

                                phase0_images = makeFolderIfNotPresent(phase0_collection, 'images to qc', '', 'collection', False, uda_user)
                                m.model('folder').setUserAccess(phase0_images, file_creator, AccessType.ADMIN, save=True)

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

                            else:

                                # just update the image
                                newitem = m.model('item').setMetadata(item, metadata=new_metadata)


                            # addItemToPhase0(possible_item[0], new_metadata)

        # not deleting original for archival purposes
        # m.model('item').remove(item)