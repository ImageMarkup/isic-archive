isic_archive.App = girder.App.extend({

    render: function () {
        this.$el.html(isic_archive.templates.layout());

        new isic_archive.views.LayoutHeaderView({
            el: this.$('#i-app-header-container'),
            parentView: this
        }).render();

        return this;
    },

    navigateTo: function () {
        this.$('#g-app-body-container').removeClass('i-body-nopad');
        return girder.App.prototype.navigateTo.apply(this, arguments);
    },

    /**
     * On login we re-render the current body view; whereas on
     * logout, we redirect to the front page.
     */
    login: function () {
        var route = girder.dialogs.splitRoute(Backbone.history.fragment).base;
        Backbone.history.fragment = null;
        girder.eventStream.close();

        if (girder.currentUser) {
            girder.eventStream.open();
            isic_archive.router.navigate(route, {trigger: true});
        } else {
            isic_archive.router.navigate('/', {trigger: true});
        }
    }
});
