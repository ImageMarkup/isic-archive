isic.App = girder.App.extend({

    render: function () {
        this.$el.html(isic.templates.layout());

        new isic.views.LayoutHeaderView({
            el: this.$('#isic-app-header-container'),
            parentView: this
        });

        return this;
    },

    navigateTo: function () {
        this.$('#g-app-body-container').removeClass('isic-body-nopad');
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
            isic.router.navigate(route, {trigger: true});
        } else {
            isic.router.navigate('/', {trigger: true});
        }
    }
});
