isic.App = girder.App.extend({

    initialize: function (settings) {
        // Call the parent "initialize", but don't let that call "start()",
        // since we want to pass custom parameters
        girder.App.prototype.initialize.call(this, {
            start: false
        });

        // Start the app (and fetch the user)
        this.start({
            // Don't render automatically, to ensure currentUser is updated
            // before the first rendering
            render: false,
            // Don't start the history, to delay starting navigation until
            // rendering has occurred
            history: false
        }).done(_.bind(function () {
            // Then update currentUser if necessary
            this._updateCurrentUser();
            // Do the things that would normally be done within "start()"
            this.render();
            Backbone.history.start({
                pushState: false
            });
        }, this));
    },

    bindGirderEvents: function () {
        girder.App.prototype.bindGirderEvents.call(this);

        // It would be better to listen for "g:login.success", as it's triggered
        // before "g:login", but "g:login.success" isn't triggered after a new
        // user registers (which is probably a bug)

        // "currentUser" must be updated before all rendering, so unbind the
        // default binding of "g:login" to "this.login", and ensure that
        // updating "currentUser" is the event bound to "g:login"; however,
        // it's an undocumented property of Backbone that events get called in
        // the order they were bound, so this isn't a great solution
        girder.events.off('g:login', this.login);
        girder.events.on('g:login', this._updateCurrentUser(), this);
        // "g:login-changed" is triggered when users change passwords
        girder.events.on('g:login-changed', this._updateCurrentUser(), this);
        girder.events.on('g:login', this.login, this);
    },

    _updateCurrentUser: function () {
        // Replace the girder.currentUser object with its subclass, which
        // exposes additional methods
        if (girder.currentUser) {
            girder.currentUser =
                new isic.models.UserModel(girder.currentUser.attributes);
        }
    },

    render: function () {
        this.$el.html(isic.templates.layout());

        new isic.views.LayoutHeaderView({ // eslint-disable-line no-new
            el: this.$('#isic-app-header-container'),
            parentView: this
        });

        new isic.views.LayoutFooterView({ // eslint-disable-line no-new
            el: this.$('#isic-app-footer-container'),
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
