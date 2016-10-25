isic.views.ImageFullscreenWidget = isic.View.extend({
    render: function () {
        this.$el.html(isic.templates.imageFullscreenWidget({
            model: this.model
        })).girderModal(this);

        new isic.views.ImageViewerWidget({ // eslint-disable-line no-new
            el: this.$('.isic-image-fullscreen-container'),
            model: this.model,
            parentView: this
        });
    }
});
