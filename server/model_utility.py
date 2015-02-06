# coding=utf-8

from girder.utility.model_importer import ModelImporter


def getCollection(collectionName):
    return ModelImporter.model('collection').findOne({'name': collectionName})


def getFolder(collection, folderName):
    return ModelImporter.model('folder').findOne({
        'parentId': collection['_id'],
        'name': folderName
    })
