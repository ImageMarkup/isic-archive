isic_archive.views.FrontPageView = girder.views.FrontPageView.extend({
    events: {
        'click .i-example-button': function () {
            isic_archive.router.navigate('example', {trigger: true});
        }
    },

    initialize: function () {
        girder.cancelRestRequests('fetch');
        this.render();
    },

    render: function () {
        this.$el.addClass('i-body-nopad');

        this.$el.html(isic_archive.templates.frontPage({
            apiRoot: girder.apiRoot,
            staticRoot: girder.staticRoot,
            currentUser: girder.currentUser,
            versionInfo: girder.versionInfo
        }));

        return this;
    }
});

isic_archive.router.route('', 'index', function () {
    girder.events.trigger('g:navigateTo', isic_archive.views.FrontPageView);
});
