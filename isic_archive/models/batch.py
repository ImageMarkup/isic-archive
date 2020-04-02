import datetime

import pymongo

from girder.models.model_base import Model


class Batch(Model):
    def initialize(self):
        self.name = 'batch'
        # TODO: add indexes

    def createBatch(self, dataset, creator, signature):
        now = datetime.datetime.utcnow()

        batch = self.save({
            'datasetId': dataset['_id'],
            'created': now,
            'creatorId': creator['_id'],
            'signature': signature,
            'ingestStatus': None,
            'uploadFileId': None
        })
        return batch

    def reingest(self, batch):
        from isic_archive.tasks import ingestImage
        from .image import Image
        # mark images as ingested=False, this needs to be done first
        # to avoid sending notifications about a batch which is "complete"
        Image().update({'meta.batchId': batch['_id']},
                       {'$set': {'ingested': False,
                                 'ingestionState': {'largeImage': None,
                                                    'superpixelMask': None}}})

        batch['ingestStatus'] = 'extracted'
        self.save(batch)

        for image in Image().find({'meta.batchId': batch['_id']}):
            ingestImage.delay(image['_id'])

    def remove(self, batch, **kwargs):
        # TODO: Remove the associated ZIP file, if one exists
        return super(Batch, self).remove(batch)

    def validate(self, doc, **kwargs):
        # TODO: implement
        return doc

    def images(self, batch):
        from .image import Image
        return Image().find({
            'meta.batchId': batch['_id'],
        })

    def hasImagesPendingIngest(self, batch):
        return self.imagesPendingIngest(batch).count() > 0

    def imagesPendingIngest(self, batch):
        from .image import Image
        return Image().find({
            'meta.batchId': batch['_id'],
            'ingested': False
        })

    def imagesFailedIngest(self, batch):
        from .image import Image
        return Image().find({
            'meta.batchId': batch['_id'],
            '$or': [
                {'ingestionState.largeImage': False},
                {'ingestionState.superpixelMask': False}
            ]
        }, fields=['privateMeta.originalFilename']).sort(
            'privateMeta.originalFilename', pymongo.ASCENDING
        )

    def imagesSkippedIngest(self, batch):
        from .image import Image
        return Image().find({
            'meta.batchId': batch['_id'],
            'readable': False
        }, fields=['privateMeta.originalFilename']).sort(
            'privateMeta.originalFilename', pymongo.ASCENDING
        )
