// Show thumbnails on the item page
girder.wrap(girder.views.ItemView, 'render', function (render) {
    // ItemView is a special case in which rendering is done asynchronously,
    // so we must listen for a render event.
    this.once('g:rendered', function () {
        // TODO: only add if this is an image item
        new girder.views.SegmentationsDisplayWidget({
            el: $('<div>', {class: '.isic-segmentations-display'})
                .insertAfter(this.$('.g-item-info')),
            parentView: this,
            itemModel: this.model
        });
    }, this);
    render.call(this);
});

girder.views.SegmentationsDisplayWidget = girder.View.extend({
    events: {
        'change select': function (event) {
            this._selectSegmentation(event.target.value);
        },
        'keyup select': function (event) {
            this._selectSegmentation(event.target.value);
        }
    },

    initialize: function (settings) {
        this.imageId = settings.itemModel.id;

        girder.restRequest({
            type: 'GET',
            path: '/segmentation?imageId=' + this.imageId
        }).done(_.bind(function (resp) {
            this.segmentations = resp;
            this.render();
        }, this));
    },

    render: function () {
        this.$el.html(girder.templates.isicSegmentationsDisplayWidget({
            segmentations: this.segmentations
        }));
    },

    _selectSegmentation: function (segmentationId) {
        if (this.segmentationDisplayWidget) {
            this.segmentationDisplayWidget.destroy();
            this.segmentationDisplayWidget = null;
        }
        if (segmentationId) {
            this.segmentationDisplayWidget = new girder.views.SegmentationDisplayWidget({
                el: this.$('.isic-segmentation-display'),
                parentView: this,
                segmentationId: segmentationId
            });
        }
    }
});

girder.views.SegmentationDisplayWidget = girder.View.extend({
    initialize: function (settings) {
        this.segmentationId = settings.segmentationId;
        this.segmentationThumbnailUrl =
            '/' + girder.apiRoot +
            '/segmentation/' + this.segmentationId +
            '/thumbnail?width=256';

        girder.restRequest({
            type: 'GET',
            path: 'segmentation/' + this.segmentationId
        }).done(_.bind(function (resp) {
            this.segmentation = resp;
            this.render();
        }, this));
    },

    render: function () {
        this.$el.html(girder.templates.isicSegmentationDisplayWidget({
            girder: girder,
            segmentation: this.segmentation,
            segmentationThumbnailUrl: this.segmentationThumbnailUrl
        }));
    }
});
