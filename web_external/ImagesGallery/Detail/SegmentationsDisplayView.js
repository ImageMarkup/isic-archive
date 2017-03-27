/**
 * View for displaying an image segmentation's properties
 */
isic.views.SegmentationDisplayView = isic.View.extend({
    /**
     * @param {isic.models.SegmentationModel} settings.model
     */
    initialize: function (settings) {
        if (this.model.has('meta')) {
            this.render();
        } else {
            // Since this view doesn't own the "model", "listenTo" absolutely must be used
            this.listenTo(this.model, 'g:fetched', this.render);
            this.model.fetch();
        }
    },

    render: function () {
        var created = girder.formatDate(this.model.get('created'), girder.DATE_SECOND);
        var thumbnailUrl = [
            girder.apiRoot,
            'segmentation',
            this.model.id,
            'thumbnail?width=256'
        ].join('/');

        this.$el.html(isic.templates.segmentationDisplayPage({
            segmentation: this.model,
            created: created,
            thumbnailUrl: thumbnailUrl,
            stringify: this._stringify
        }));

        return this;
    },

    _stringify: function (val) {
        return JSON.stringify(val, null, 4);
    }
});

/**
 * View for selecting an image segmentation and displaying its properties
 */
isic.views.SegmentationsDisplayView = isic.View.extend({
    events: {
        'change select': function (event) {
            var selectedSegmentationId = $(event.currentTarget).val();
            var selectedSegmentation = this.segmentations.get(selectedSegmentationId);
            selectedSegmentation.select();
        }
    },

    /**
     * @param {isic.models.ImageModel} settings.image
     */
    initialize: function (settings) {
        this.image = settings.image;

        this.segmentations = new isic.collections.SelectableSegmentationCollection();
        this.listenTo(this.segmentations, 'g:changed', this.render);
        this.listenTo(this.segmentations, 'select:one', this.onSelected);

        this.segmentationDisplayView = null;

        this.segmentations.fetch({
            imageId: this.image.id,
            limit: 0
        });
    },

    render: function () {
        this.$el.html(isic.templates.segmentationsDisplayPage({
            segmentations: this.segmentations.models
        }));

        return this;
    },

    onSelected: function (selectedSegmentation) {
        if (this.segmentationDisplayView) {
            this.segmentationDisplayView.destroy();
            this.segmentationDisplayView = null;
        }
        this.segmentationDisplayView = new isic.views.SegmentationDisplayView({
            model: selectedSegmentation,
            el: this.$('#isic-segmentation-display-container'),
            parentView: this
        });
    }
});
