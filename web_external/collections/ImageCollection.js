isic.collections.ImageCollection = isic.Collection.extend({
    resourceName: 'image',
    model: isic.models.ImageModel
});

isic.collections.SelectableImageCollection = isic.collections.ImageCollection.extend({
    initialize: function (models) {
        Backbone.Select.One.applyTo(this, models);
        isic.collections.ImageCollection.prototype.initialize.apply(this, arguments);
    }
});
