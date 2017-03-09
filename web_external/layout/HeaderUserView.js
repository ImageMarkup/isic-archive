isic.views.LayoutHeaderUserView = isic.View.extend({
    events: {
        'click a.g-login': function () {
            girder.events.trigger('g:loginUi');
        },

        'click a.g-register': function () {
            girder.events.trigger('g:registerUi');
        },

        'click a.g-logout': function () {
            girder.restRequest({
                path: 'user/authentication',
                type: 'DELETE'
            }).done(_.bind(function () {
                girder.currentUser = null;
                girder.events.trigger('g:login');
            }, this));
        },

        'click a.g-my-settings': function () {
            isic.router.navigate('useraccount/' + girder.currentUser.id +
                                    '/info', {trigger: true});
        }
    },

    render: function () {
        this.$el.html(isic.templates.layoutHeaderUser({
            user: girder.currentUser
        }));

        if (girder.currentUser) {
            this.$('.isic-portrait-wrapper').css(
                'background-image', 'url(' +
                girder.currentUser.getGravatarUrl(36) + ')');
        }
        return this;
    }
});
