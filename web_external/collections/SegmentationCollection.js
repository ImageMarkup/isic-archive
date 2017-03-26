isic.collections.SegmentationCollection = isic.Collection.extend({
    resourceName: 'segmentation',
    model: isic.models.SegmentationModel,
    sortField: 'created',
    sortDir: girder.SORT_DESC
});

isic.collections.SelectableSegmentationCollection = isic.collections.SegmentationCollection.extend({
    initialize: function (models) {
        Backbone.Select.One.applyTo(this, models);
        isic.collections.SegmentationCollection.prototype.initialize.apply(this, arguments);
    }
});
