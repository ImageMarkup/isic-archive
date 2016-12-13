isic.collections.SegmentationCollection = girder.Collection.extend({
    resourceName: 'segmentation',
    model: isic.models.SegmentationModel,
    sortField: 'created',
    sortDir: girder.SORT_DESC
});
