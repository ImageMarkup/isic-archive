// Show thumbnails on the item page
girder.wrap(girder.views.ItemView, 'render', function (render) {
    // ItemView is a special case in which rendering is done asynchronously,
    // so we must listen for a render event.
    this.once('g:rendered', function () {
        // TODO: only add if this is an image item
        new girder.views.ThumbnailWidget({
            el: $('<div>', {class: '.g-item-thumbnail'})
                .insertAfter(this.$('.g-item-info')),
            parentView: this,
            itemModel: this.model
        });
    }, this);
    render.call(this);
});

girder.views.ThumbnailWidget = girder.View.extend({
    initialize: function (settings) {
        this.itemModel = settings.itemModel;
        this.render();
    },

    render: function () {
        this.$el.html(girder.templates.thumbnail({
            thumbnailSrc: '/api/v1/image/' + this.itemModel.id + '/thumbnail'
        }));
    }
});
