isic.views.ImagesViewSubViews = isic.views.ImagesViewSubViews || {};

// View for image details
isic.views.ImagesViewSubViews.ImageDetailsPane = isic.View.extend({
    events: {
        'click .button': 'clearSelectedImage',
        'click .openwindow': 'openwindow',
        'click .zoom': 'zoom'
    },

    initialize: function (settings) {
        this.image = settings.image;

        this.listenTo(this.image, 'changed:_id g:fetched g:error', this.render);

        this.segmentationsDisplayView = new isic.views.SegmentationsDisplayView({
            image: this.image,
            parentView: this
        });
    },

    render: function () {
        var created = null;
        var license = {
            name: null,
            url: null
        };
        var acquisitionMetadata = null;
        var clinicalMetadata = null;
        var unstructuredMetadata = null;

        // Get image data
        if (this.image.id) {
            created = girder.formatDate(this.image.get('created'), girder.DATE_SECOND);

            // Get license, default to CC-0
            if (this.image.has('license')) {
                license.name = this.image.get('license');
            } else {
                license.name = 'CC-0';
                license.url = 'https://creativecommons.org/publicdomain/zero/1.0/';
            }

            var meta = this.image.get('meta');
            acquisitionMetadata = meta['acquisition'];
            clinicalMetadata = meta['clinical'];
            unstructuredMetadata = meta['unstructured'] || {};

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
            license: license,
            acquisitionMetadata: acquisitionMetadata,
            clinicalMetadata: clinicalMetadata,
            unstructuredMetadata: unstructuredMetadata
        }));

        this.segmentationsDisplayView.setElement(
            this.$('#isic-image-details-segmentations-display-view-container')).render();

        this.initializeTooltips();

        return this;
    },

    openwindow: function () {
        this.clearTooltips();
        window.open('/api/v1/image/' + this.image.id + '/download?contentDisposition=inline');
    },

    zoom: function () {
      this.clearTooltips();
      isic.util.imagesModal(this.image.id);
    },

    clearSelectedImage: function () {
        this.image.clear();
    },

    initializeTooltips: function () {
        this.$('[data-toggle="tooltip"]').tooltip({
            trigger: 'hover'
        });
    },

    clearTooltips: function () {
        $('[data-toggle="tooltip"]').tooltip('hide');
    }
});
