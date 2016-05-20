isic_archive.views.ExampleView = isic_archive.View.extend({
    initialize: function (settings) {
        girder.cancelRestRequests('fetch');
        this.render();
    },

    render: function () {
        this.$el.html(isic_archive.templates.examplePage({
            user: girder.currentUser
        }));

        return this;
    }
});

isic_archive.router.route('example', 'example', function (id) {
    girder.events.trigger('g:navigateTo', isic_archive.views.ExampleView);
});
