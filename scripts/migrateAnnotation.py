from girder.utility import server as girder_server
girder_server.configureServer()

from girder.models.item import Item  # noqa: E402
from girder.models.folder import Folder  # noqa: E402
from girder.plugins.isic_archive.models.annotation import Annotation  # noqa: E402
from girder.plugins.isic_archive.models.study import Study  # noqa: E402

for annotationItem in Item().find({
    'baseParentId': Study().loadStudyCollection()['_id']
}):
    Annotation().save({
        '_id': annotationItem['_id'],
        'studyId': annotationItem['meta']['studyId'],
        'imageId': annotationItem['meta']['imageId'],
        'userId': annotationItem['meta']['userId'],
        'startTime': annotationItem['meta'].get('startTime', None),
        'stopTime': annotationItem['meta'].get('stopTime', None),
        'status': annotationItem['meta'].get('status', None),
        'annotations': annotationItem['meta'].get('annotations', None),
    })

for studyAnnotatorFolder in Folder().find({
    'baseParentId': Study().loadStudyCollection()['_id'],
    'meta.userId': {'$exists': 1}
}):
    Folder().remove(studyAnnotatorFolder)
