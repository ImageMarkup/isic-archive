from girder.utility import server as girder_server
girder_server.configureServer()

from girder.models.item import Item  # noqa: E402
from girder.models.folder import Folder  # noqa: E402
from girder.plugins.isic_archive.models.annotation import Annotation  # noqa: E402
from girder.plugins.isic_archive.models.study import Study  # noqa: E402

for annotationItem in Item().find({
    'baseParentId': Study().loadStudyCollection()['_id']
}):
    dataset = Annotation().save({
        '_id': annotationItem['_id'],
        'studyId': annotationItem['meta']['studyId'],
        'imageId': annotationItem['meta']['studyId'],
        'userId': annotationItem['meta']['studyId'],
        'startTime': annotationItem['meta']['startTime'],
        'stopTime': annotationItem['meta']['stopTime'],
        'status': annotationItem['meta']['status'],
        'annotations': annotationItem['meta']['annotations'],
    })

for studyAnnotatorFolder in Folder().find({
    'baseParentId': Study().loadStudyCollection()['_id'],
    'meta.userId': {'$exists': 1}
}):
    Folder().remove(studyAnnotatorFolder)
