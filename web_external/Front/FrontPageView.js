isic.views.FrontPageView = girder.views.FrontPageView.extend({
    initialize: function (settings) {
        this.render();
    },

    render: function () {
        this.$el.html(isic.templates.frontPage({
            staticImageRoot: girder.staticRoot + '/built/plugins/isic_archive/extra/img'
        }));

        return this;
    }
});

isic.router.route('', 'index', function () {
    girder.events.trigger('g:navigateTo', isic.views.FrontPageView);
});
