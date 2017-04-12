isic.views.InvitationConfirmationView = isic.View.extend({
    events: {
        'click #isic-invitation-confirmation-invite-user': function (event) {
            girder.events.trigger('g:navigateTo', isic.views.InviteUserView);
        }
    },

    /**
     * @param {Object} settings.newUser - Information about the new user.
     * @param {string} settings.inviteUrl - The URL of the invitation sent to the new user.
     */
    initialize: function (settings) {
        this.newUser = settings.newUser;
        this.inviteUrl = settings.inviteUrl;

        this.render();
    },

    render: function () {
        this.$el.html(isic.templates.invitationConfirmationPage({
            newUser: this.newUser,
            inviteUrl: this.inviteUrl
        }));

        return this;
    }
});
