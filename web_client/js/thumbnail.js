girder.views.ThumbnailWidget = girder.View.extend({
    initialize: function (settings) {
        this.itemModel = settings.imageModel;
        // TODO: find a better way to determine if this Item is an Image
        if (this.itemModel.get('largeImage')) {
            this.render();
        }
    },

    render: function () {
        this.$el.html(girder.templates.thumbnail({
            thumbnailSrc: '/api/v1/image/' + this.itemModel.id + '/thumbnail'
        }));
    }
});

// Hijack the large_image's 'ImageViewerSelectWidget' to render ThumbnailWidget
// and hide the default viewers in 'ImageViewerSelectWidget'
girder.views.ImageViewerSelectWidget = girder.views.ThumbnailWidget;
