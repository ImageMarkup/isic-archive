isic.views.ImagesSubViews = isic.views.ImagesSubViews || {};

// View for image details
isic.views.ImagesSubViews.ImageDetailsPane = Backbone.View.extend({
    events: {
        'click .button': 'clearSelectedImage'
    },

    initialize: function () {
        this.image = new isic.models.ImageModel();
        this.listenTo(this.image, 'change', this.render);
        this.listenTo(this.model, 'change:selectedImageId', this.fetchImage);
    },

    render: function () {
        // Get metadata from image
        var acquisitionMetadata = null;
        var clinicalMetadata = null;
        if (this.image.has('meta')) {
            var meta = this.image.get('meta');
            if (_.has(meta, 'acquisition')) {
                acquisitionMetadata = meta['acquisition'];
            }
            if (_.has(meta, 'clinical')) {
                clinicalMetadata = meta['clinical'];
            }
        }

        this.$el.html(isic.templates.imageDetailsPage({
            imgRoot: girder.staticRoot + '/built/plugins/isic_archive/extra/img',
            image: this.image,
            acquisitionMetadata: acquisitionMetadata,
            clinicalMetadata: clinicalMetadata
        }));

        return this;
    },

    clearSelectedImage: function () {
        this.model.set('selectedImageId', null);
    },

    fetchImage: function () {
        var imageId = this.model.get('selectedImageId');
        if (imageId) {
            this.image.set('_id', imageId);
            this.image.fetch();
        } else {
            this.image.clear();
        }
    }
});
