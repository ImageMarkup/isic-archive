isic.views.FrontPageView = girder.views.FrontPageView.extend({
    events: {
        'click .i-example-button': function () {
            isic.router.navigate('example', {trigger: true});
        }
    },

    initialize: function () {
        girder.cancelRestRequests('fetch');
        this.render();
    },

    render: function () {
        this.$el.addClass('i-body-nopad');

        this.$el.html(isic.templates.frontPage({
            apiRoot: girder.apiRoot,
            staticRoot: girder.staticRoot,
            currentUser: girder.currentUser,
            versionInfo: girder.versionInfo
        }));

        return this;
    }
});

isic.router.route('', 'index', function () {
    girder.events.trigger('g:navigateTo', isic.views.FrontPageView);
});
