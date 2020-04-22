from girder.models.file import File

from isic_archive.models.image import Image

for i, img in enumerate(Image().find()):
    print(i, img['name'])

    for childFile in Image().childFiles(img):
        if childFile['imageRole'] == 'scrapped':
            File().remove(childFile)
            print(f'Removed {childFile["name"]}')
