isic.views.ExampleView = isic.View.extend({
    initialize: function (settings) {
        girder.cancelRestRequests('fetch');
        this.render();
    },

    render: function () {
        this.$el.html(isic.templates.examplePage({
            user: girder.currentUser
        }));

        return this;
    }
});

isic.router.route('example', 'example', function (id) {
    girder.events.trigger('g:navigateTo', isic.views.ExampleView);
});
