isic.collections.SegmentationCollection = isic.Collection.extend({
    resourceName: 'segmentation',
    model: isic.models.SegmentationModel,
    sortField: 'created',
    sortDir: girder.SORT_DESC
});
