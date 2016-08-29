isic.views.ImagesViewSubViews = isic.views.ImagesViewSubViews || {};

// View for image details
isic.views.ImagesViewSubViews.ImageDetailsPane = isic.View.extend({
    events: {
        'click .button': 'clearSelectedImage'
    },

    initialize: function () {
        this.image = new isic.models.ImageModel();
        this.listenTo(this.image, 'g:fetched g:error', this.render);
        this.listenTo(this.model, 'change:selectedImageId', this.selectedImageChanged);

        this.segmentationsDisplayView = new isic.views.SegmentationsDisplayView({
            image: this.image,
            parentView: this
        });
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
            acquisitionMetadata['Dimensions (pixels)'] =
                acquisitionMetadata['pixelsX'] + ' &times; ' + acquisitionMetadata['pixelsY'];
            delete acquisitionMetadata['pixelsX'];
            delete acquisitionMetadata['pixelsY'];
        }

        this.$el.html(isic.templates.imageDetailsPage({
            imgRoot: girder.staticRoot + '/built/plugins/isic_archive/extra/img',
            image: this.image,
            created: created,
            acquisitionMetadata: acquisitionMetadata,
            clinicalMetadata: clinicalMetadata
        }));

        this.segmentationsDisplayView.setElement(
            this.$('#isic-image-details-segmentations-display-view-container')).render();

        return this;
    },

    clearSelectedImage: function () {
        this.model.set('selectedImageId', null);
    },

    selectedImageChanged: function () {
        var imageId = this.model.get('selectedImageId');

        // Fetch or clear image details
        if (imageId) {
            this.image.set('_id', imageId);
            this.image.fetch();
        } else {
            this.image.clear();
        }
    }
});
