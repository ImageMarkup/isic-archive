isic.views.ImagesView = isic.View.extend({
    events: {
    },

    initialize: function (settings) {
        this.render();
    },

    render: function () {
        this.$el.html(isic.templates.imagesPage({
        }));

        return this;
    }
});

isic.router.route('images', 'images', function (id) {
    girder.events.trigger('g:navigateTo', isic.views.ImagesView);
});
