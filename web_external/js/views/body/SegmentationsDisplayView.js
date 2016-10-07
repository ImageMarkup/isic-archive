//
// Segmentations display view
//

// View for displaying an image segmentation's properties
isic.views.SegmentationDisplayView = isic.View.extend({
    initialize: function (settings) {
        this.listenTo(this.model, 'change:_id g:fetched g:error', this.render);

        this.render();
    },

    render: function () {
        var created = null;
        var thumbnailUrl = null;

        if (this.model.id) {
            created = girder.formatDate(this.model.get('created'), girder.DATE_SECOND);
            thumbnailUrl = [
                girder.apiRoot,
                'segmentation',
                this.model.id,
                'thumbnail?width=256'
            ].join('/');
        }

        this.$el.html(isic.templates.segmentationDisplayPage({
            segmentation: this.model,
            created: created,
            thumbnailUrl: thumbnailUrl,
            formatUser: this.formatUser
        }));

        return this;
    }
});

// View for selecting an image segmentation and displaying its properties
isic.views.SegmentationsDisplayView = isic.View.extend({
    events: {
        'change select': function (event) {
            var segmentationId = $(event.currentTarget).val();
            this.segmentation.set('_id', segmentationId, {silent: true});
            this.segmentation.fetch();
        }
    },

    initialize: function (settings) {
        this.image = settings.image;

        this.segmentations = new isic.collections.SegmentationCollection();

        this.segmentation = new isic.models.SegmentationModel();

        this.segmentationDisplayView = new isic.views.SegmentationDisplayView({
            model: this.segmentation,
            parentView: this
        });

        this.listenTo(this.image, 'change:_id', this.fetchSegmentations);

        this.render();
    },

    render: function () {
        this.$el.html(isic.templates.segmentationsDisplayPage({
            segmentations: this.segmentations.models
        }));

        this.segmentationDisplayView.setElement(
            this.$('#isic-segmentation-display-container')).render();

        return this;
    },

    fetchSegmentations: function () {
        this.segmentation.clear();
        this.segmentations.reset();

        this.render();

        if (this.image.id) {
            // upstream Girder contains a bug where parameters are not honored
            // on a reset fetch, so reset "offset" outside of fetch
            this.segmentations.offset = 0;
            this.segmentations.once('g:changed', _.bind(function () {
                this.render();
            }, this)).fetch({
                imageId: this.image.id,
                limit: 0
            });
        }
    }
});
