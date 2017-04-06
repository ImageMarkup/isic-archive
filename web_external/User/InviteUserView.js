isic.views.InviteUserView = isic.View.extend({
    events: {
        'submit #isic-user-invite-form': function (event) {
            event.preventDefault();
            // this.$('#isic-user-invite-submit').prop('disabled', true);

            girder.restRequest({
                path: 'user/invite',
                data: {
                    login: this.$('#isic-user-invite-new-login').val(),
                    email: this.$('#isic-user-invite-new-email').val(),
                    firstName: this.$('#isic-user-invite-new-firstname').val(),
                    lastName: this.$('#isic-user-invite-new-lastname').val()
                },
                type: 'POST',
                error: null
            })
                .done(function (resp) {
                    console.log('success', resp);
                })
                .fail(function (resp) {
                    isic.showAlertDialog({
                        text: '<h4>Error sending invite</h4><br>' + _.escape(resp.responseJSON.message),
                        escapedHtml: true
                    });
                });
        }
    },

    /**
     */
    initialize: function (settings) {
        this.render();
    },

    render: function () {
        this.$el.html(isic.templates.inviteUserPage());

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
