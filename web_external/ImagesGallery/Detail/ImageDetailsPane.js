isic.views.ImageDetailsPane = isic.View.extend({
    events: {
        'click #isic-image-details-zoom': 'zoom',
        'click #isic-image-details-close': 'clearSelectedImage'
    },

    /**
     * @param {isic.collections.SelectableImageCollection} settings.images
     */
    initialize: function (settings) {
        this.images = settings.images;
        this.segmentationsDisplayView = null;

        // Collection resets do not trigger "deselect" events, so they must be listened for
        this.listenTo(this.images, 'select:one', this.render);
        this.listenTo(this.images, 'deselect:one reset', this.onDeselected);
    },

    onDeselected: function (model, collection, options) {
        // If another image is selected, do nothing, as the "select:one" event has already triggered
        if (!this.images.selected) {
            this.$el.hide();
            if (this.segmentationsDisplayView) {
                this.segmentationsDisplayView.destroy();
                this.segmentationsDisplayView = null;
            }
            this.$el.empty();
        }
    },

    render: function () {
        var selectedImage = this.images.selected;
        if (!selectedImage) {
            // Guard in case a deselection happened while a fetch was pending
            return;
        }

        if (!selectedImage.has('meta')) {
            // If the image is only a summary, fetch details, then render
            // TODO: a loading widget could be displayed, instead of an empty div
            this.$el.empty();
            selectedImage
                .once('g:fetched', this.render, this)
                .fetch();
            return;
        }

        // Get image data
        var created = girder.formatDate(selectedImage.get('created'), girder.DATE_SECOND);

        // Get license, default to CC-0
        var license;
        if (selectedImage.has('license')) {
            license = {
                name: selectedImage.get('license'),
                url: null
            };
        } else {
            license = {
                name: 'CC-0',
                url: 'https://creativecommons.org/publicdomain/zero/1.0/'
            };
        }

        var meta = selectedImage.get('meta');
        var acquisitionMetadata = meta['acquisition'];
        var clinicalMetadata = meta['clinical'];
        var unstructuredMetadata = meta['unstructured'] || {};
        var privateMetadata = selectedImage.get('privateMeta');

        // Reformat some acquisition metadata
        acquisitionMetadata = _.clone(acquisitionMetadata);
        acquisitionMetadata['Dimensions (pixels)'] =
            acquisitionMetadata['pixelsX'] + ' &times; ' + acquisitionMetadata['pixelsY'];
        delete acquisitionMetadata['pixelsX'];
        delete acquisitionMetadata['pixelsY'];

        this.$el.html(isic.templates.imageDetailsPage({
            apiRoot: girder.apiRoot,
            imgRoot: girder.staticRoot + '/built/plugins/isic_archive/extra/img',
            image: selectedImage,
            currentUser: girder.currentUser,
            created: created,
            license: license,
            acquisitionMetadata: acquisitionMetadata,
            clinicalMetadata: clinicalMetadata,
            unstructuredMetadata: unstructuredMetadata,
            privateMetadata: privateMetadata
        }));

        this.segmentationsDisplayView = new isic.views.SegmentationsDisplayView({
            image: selectedImage,
            el: this.$('#isic-image-details-segmentations-display-view-container'),
            parentView: this
        });

        this.$('[data-toggle="tooltip"]').tooltip({
            trigger: 'hover'
        });

        this.$el.show();

        return this;
    },

    zoom: function () {
        this.clearTooltips();
        new isic.views.ImageFullscreenWidget({ // eslint-disable-line no-new
            el: $('#g-dialog-container'),
            model: this.images.selected,
            parentView: this
        }).render();
    },

    clearSelectedImage: function () {
        this.images.deselect();
    },

    clearTooltips: function () {
        $('[data-toggle="tooltip"]').tooltip('hide');
    }
});
