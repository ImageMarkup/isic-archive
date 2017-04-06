isic.views.RsvpUserView = isic.View.extend({
    events: {
        'submit #isic-user-rsvp-form': function (event) {
            event.preventDefault();

            if (this.$('#isic-user-rsvp-password').val() !== this.$('#isic-user-rsvp-password2').val()) {
                isic.showAlertDialog({
                    text: 'Passwords do not match, try again.',
                    callback: _.bind(function () {
                        this.$('#isic-user-rsvp-password,#isic-user-rsvp-password2').val('');
                        this.$('#isic-user-rsvp-password').focus();
                    }, this)
                });
                return;
            }

            this.user
                .changePassword(
                    this.token,
                    this.$('#g-password-new').val()
                )
                .done(function () {
                    isic.router.navigate('tasks', {trigger: true});
                })
                .fail(function (resp) {
                    isic.showAlertDialog({
                        text: '<h4>Error changing password</h4><br>' + _.escape(resp.responseJSON.message),
                        escapedHtml: true
                    });
                });
        }
    },

    /**
     * @param {isic.models.UserModel} settings.user - The user to complete registration for.
     * @param {string} settings.token - The user to complete registration for.
     */
    initialize: function (settings) {
        this.user = settings.user;
        this.token = settings.token;

        this.render();
    },

    render: function () {
        this.$el.html(isic.templates.rsvpUserPage({
            user: this.user
        }));

        return this;
    }
});

isic.router.route('user/:id/rsvp/:token', 'rsvpUser', function (id, token) {
    isic.models.UserModel
        .temporaryTokenLogin(id, token)
        .done(function (resp) {
            girder.events.trigger('g:navigateTo', girder.views.RsvpUserView, {
                user: girder.currentUser,
                token: token
            });
        })
        .fail(function () {
            isic.showAlertDialog({
                text: '<h4>Error loading user from token</h4><br>' + _.escape(resp.responseJSON.message),
                escapedHtml: true
            });
            girder.router.navigate('', {trigger: true});
        });
});
