isic.views.ImageDetailsPane = isic.View.extend({
    events: {
        'click #isic-image-details-zoom': 'zoom',
        'click #isic-image-details-close': 'closeDetails'
    },

    /**
     * @param {isic.models.ImageModel} settings.image
     */
    initialize: function (settings) {
        this.image = settings.image;

        if (!this.image.has('meta')) {
            // If the image is only a summary, fetch details, then render
            // Since this view doesn't own the "image", "listenTo" absolutely must be used
            this.listenTo(this.image, 'g:fetched', this.render);
            this.image.fetch();
            // TODO: a loading widget could be displayed while the fetch runs
        } else {
            this.render();
        }
    },

    render: function () {
        // Get image data
        var created = girder.formatDate(this.image.get('created'), girder.DATE_SECOND);

        // Get license, default to CC-0
        var license;
        if (this.image.has('license')) {
            license = {
                name: this.image.get('license'),
                url: null
            };
        } else {
            license = {
                name: 'CC-0',
                url: 'https://creativecommons.org/publicdomain/zero/1.0/'
            };
        }

        this.$el.html(isic.templates.imageDetailsPage({
            apiRoot: girder.apiRoot,
            image: this.image,
            currentUser: girder.currentUser,
            created: created,
            license: license,
            _: _
        }));

        this.segmentationsDisplayView = new isic.views.SegmentationsDisplayView({
            image: this.image,
            el: this.$('#isic-image-details-segmentations-display-view-container'),
            parentView: this
        });

        this.$('[data-toggle="tooltip"]').tooltip({
            trigger: 'hover'
        });

        return this;
    },

    zoom: function () {
        this.clearTooltips();
        new isic.views.ImageFullscreenWidget({ // eslint-disable-line no-new
            el: $('#g-dialog-container'),
            model: this.image,
            parentView: this
        }).render();
    },

    closeDetails: function () {
        this.image.deselect();
    },

    clearTooltips: function () {
        $('[data-toggle="tooltip"]').tooltip('hide');
    }
});
