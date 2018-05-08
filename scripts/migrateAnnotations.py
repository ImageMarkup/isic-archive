from girder.utility import server as girder_server
girder_server.configureServer()

from girder.plugins.isic_archive.models.annotation import Annotation  # noqa: E402
from girder.plugins.isic_archive.models.study import Study  # noqa: E402

for study in Study().find():
    print study['name']

    for annotation in Annotation().find({'studyId': study['_id']}):
        print ' ', annotation['_id']

        oldSuperpixelsMarkups = annotation['markups']

        annotation['markups'] = {}
        for featureId, superpixelValues in oldSuperpixelsMarkups:
            annotation = Annotation().saveSuperpixelMarkup(annotation, featureId, superpixelValues)
