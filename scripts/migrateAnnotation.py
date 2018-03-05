from girder.utility import server as girder_server
girder_server.configureServer()

from girder.plugins.isic_archive.models.annotation import Annotation  # noqa: E402

for annotation in Annotation().find():
    annotation['markups'] = {}
    annotation['responses'] = {}

    markups = annotation.pop('annotations')
    if markups is not None:
        for markupName, markupValue in markups.items():
            if isinstance(markupValue, list):
                annotation['markups'][markupName] = markupValue
            else:
                annotation['responses'][markupName] = markupValue

    Annotation().save(annotation, validate=False)
