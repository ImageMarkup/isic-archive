import pprint
import re

from bson.objectid import ObjectId
from girder.utility import server as girder_server  # noqa

girder_server.configureServer()  # noqa
from girder.models.file import File  # noqa
from girder.models.item import Item  # noqa

from isic_archive.models.dataset import Dataset  # noqa: E402


for image in Item().find(
    {'baseParentId': ObjectId('55943cff9fc3c13155bcad5e')}
):
    dataset = Dataset().find({'_id': image['meta']['datasetId']})
    print(f'{image["name"]}, {image["_id"]}, {next(dataset)["name"]}')
    files = list(File().find({'itemId': image['_id']}))
    taken_file_ids = set()

    superpixel_file_ids = [
        f['_id']
        for f in files
        if 'superpixels' in f['name']
        and f['size'] > 0
        and f['_id'] not in taken_file_ids
    ]
    taken_file_ids = taken_file_ids.union(set(superpixel_file_ids))

    exif_file_ids = [
        f['_id']
        for f in files
        if '.stripped.' in f['name']
        and f['size'] > 0
        and f['_id'] not in taken_file_ids
    ]
    taken_file_ids = taken_file_ids.union(set(exif_file_ids))

    large_image_file_id = (
        image['largeImage']['fileId'] if 'largeImage' in image else None
    )
    if large_image_file_id:
        assert large_image_file_id not in taken_file_ids
        taken_file_ids = taken_file_ids.union(set([large_image_file_id]))

    original_files = [
        f
        for f in files
        if re.match(r'^ISIC_\d{7}\.[^.]+$', f['name'])
        and f['_id'] not in taken_file_ids
    ]

    def guess_original(files):
        if len(files) == 2 and set([x['mimeType'] for x in files]) == set(
            ['image/jpeg', 'image/tiff']
        ):
            return [x for x in files if x['mimeType'] == 'image/jpeg'][0]['_id']

    # this happens with the VSHR dataset
    if len(original_files) > 1:
        # if not identical files
        if not len(set([x['sha512'] for x in original_files])) == 1:
            original_file_id = guess_original(original_files)
        else:
            original_file_id = original_files[0]['_id']
    else:
        original_file_id = original_files[0]['_id']

    assert original_file_id, pprint.pformat(original_files)
    taken_file_ids = taken_file_ids.union(set([original_file_id]))

    found_original = False
    for file_ in sorted(files, key=lambda x: x['name']):
        if superpixel_file_ids and file_['_id'] in superpixel_file_ids:  # VSHR dataset
            role = 'superpixel'
        elif large_image_file_id and file_['_id'] == large_image_file_id:
            role = 'large_image'
        elif (
            exif_file_ids and file_['_id'] in exif_file_ids
        ):  # certain MSK images have duplicate exif files
            role = 'exif'
        elif file_['_id'] == original_file_id:
            role = 'original'
            found_original = True
        else:
            role = 'scrapped'
        print(f'{file_["name"]:50} -> {role}')
        file_['imageRole'] = role
        File().updateFile(file_)
    assert found_original

    print()
