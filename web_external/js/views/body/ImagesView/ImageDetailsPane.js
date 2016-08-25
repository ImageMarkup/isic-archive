isic.views.ImagesViewSubViews = isic.views.ImagesViewSubViews || {};

// View for image details
isic.views.ImagesViewSubViews.ImageDetailsPane = Backbone.View.extend({
    events: {
        'click .button': 'clearSelectedImage'
    },
    initialize: function () {
        this.image = new isic.models.ImageModel();
        this.listenTo(this.image, 'g:fetched', this.render);
        this.listenTo(this.model, 'change:selectedImageId', this.fetchImage);
    },

    render: function () {
        var created = null;
        var acquisitionMetadata = null;
        var clinicalMetadata = null;

        // Get image data
        if (this.image.id) {
            created = girder.formatDate(this.image.get('created'), girder.DATE_SECOND);
            var meta = this.image.get('meta');
            acquisitionMetadata = meta['acquisition'];
            clinicalMetadata = meta['clinical'];

            // Reformat some acquisition metadata
            if (_.has(acquisitionMetadata, 'pixelsX') &&
                _.has(acquisitionMetadata, 'pixelsY')) {
                acquisitionMetadata['Dimensions (pixels)'] =
                    acquisitionMetadata['pixelsX'] + ' &times; ' + acquisitionMetadata['pixelsY'];
                delete acquisitionMetadata['pixelsX'];
                delete acquisitionMetadata['pixelsY'];
            }
        }

        this.$el.html(isic.templates.imageDetailsPage({
            imgRoot: girder.staticRoot + '/built/plugins/isic_archive/extra/img',
            image: this.image,
            created: created,
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
