isic.views.InviteUserView = isic.View.extend({
    events: {
        'submit #isic-user-invite-form': function (event) {
            event.preventDefault();
            this.$('#isic-user-invite-submit').prop('disabled', true);

            var data = {
                login: this.$('#isic-user-invite-new-login').val(),
                email: this.$('#isic-user-invite-new-email').val(),
                firstName: this.$('#isic-user-invite-new-firstname').val(),
                lastName: this.$('#isic-user-invite-new-lastname').val()
            };

            var validityPeriod = this.$('#isic-user-invite-period').val();
            if (validityPeriod.trim().length > 0) {
                data.validityPeriod = validityPeriod;
            }

            girder.restRequest({
                path: 'user/invite',
                data: data,
                type: 'POST',
                error: null
            })
            .done(_.bind(function (resp) {
                this.confirmation = _.clone(resp);
                this.confirmation.newUser.email = data.email;
                this.render();
                isic.router.navigate('user/invite?confirmation=true', {replace: true});
            }, this))
            .fail(_.bind(function (resp) {
                isic.showAlertDialog({
                    text: '<h4>Error sending invite</h4><br>' + _.escape(resp.responseJSON.message),
                    escapedHtml: true
                });
                this.$('#isic-user-invite-submit').prop('disabled', false);
            }, this));
        },
        'click #isic-invitation-confirmation-invite-user': function (event) {
            this.confirmation = null;
            this.render();
            isic.router.navigate('user/invite', {replace: true});
        }
    },

    /**
     */
    initialize: function (settings) {
        this.confirmation = null;
        this.render();
    },

    render: function () {
        if (this.confirmation) {
            this.$el.html(isic.templates.invitationConfirmationPage({
                newUser: this.confirmation.newUser,
                inviteUrl: this.confirmation.inviteUrl
            }));
        } else {
            this.$el.html(isic.templates.inviteUserPage());
            this.$('#isic-user-invite-new-login').focus();
        }

        return this;
    }
});

isic.router.route('user/invite', 'inviteUser', function () {
    // Route to index if user isn't a study administrator
    if (girder.currentUser && girder.currentUser.canAdminStudy()) {
        girder.events.trigger('g:navigateTo', isic.views.InviteUserView);
    } else {
        isic.router.navigate('', {trigger: true});
    }
});
