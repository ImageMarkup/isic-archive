import json
import os
import sys

from girder.utility import server as girder_server

from isic_archive.models.annotation import Annotation

girder_server.configureServer()


input_directory = sys.argv[1]

for annotation_file in os.listdir(input_directory):
    with open(annotation_file) as infile:
        annotation = Annotation().load(annotation_file.replace(".json", ""), force=True)
        annotation_data = json.load(infile)

        for featureId, superpixelValues in annotation_data["markups"].items():
            Annotation().saveSuperpixelMarkup(annotation, featureId, superpixelValues)
