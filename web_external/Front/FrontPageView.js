isic.views.FrontPageView = girder.views.FrontPageView.extend({
    initialize: function (settings) {
        this.render();
    },

    render: function () {
        this.$el.html(isic.templates.frontPage({
            apiRoot: girder.apiRoot,
            staticRoot: girder.staticRoot,
            versionInfo: girder.versionInfo
        }));

        return this;
    }
});

isic.router.route('', 'index', function () {
    girder.events.trigger('g:navigateTo', isic.views.FrontPageView);
});
