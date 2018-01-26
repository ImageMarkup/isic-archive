import _ from 'underscore';

import {restRequest} from 'girder/rest';

import View from '../view';
import router from '../router';
import {showAlertDialog} from '../common/utilities';

import InvitationConfirmationPageTemplate from './invitationConfirmationPage.pug';
import './invitationConfirmationPage.styl';
import InviteUserPageTemplate from './inviteUserPage.pug';
import './inviteUserPage.styl';

const InviteUserView = View.extend({
    events: {
        'submit #isic-user-invite-form': function (event) {
            event.preventDefault();
            this.$('#isic-user-invite-submit').girderEnable(false);

            let data = {
                login: this.$('#isic-user-invite-new-login').val(),
                email: this.$('#isic-user-invite-new-email').val(),
                firstName: this.$('#isic-user-invite-new-firstname').val(),
                lastName: this.$('#isic-user-invite-new-lastname').val()
            };

            let validityPeriod = this.$('#isic-user-invite-period').val();
            if (validityPeriod.trim().length > 0) {
                data.validityPeriod = validityPeriod;
            }

            restRequest({
                url: 'user/invite',
                data: data,
                method: 'POST',
                error: null
            })
                .done((resp) => {
                    this.confirmation = resp;
                    this.confirmation.newUser.email = data.email;
                    this.render();
                    router.navigate('user/invite?confirmation=true', {replace: true});
                })
                .fail((resp) => {
                    showAlertDialog({
                        text: `<h4>Error sending invite</h4><br>${_.escape(resp.responseJSON.message)}`,
                        escapedHtml: true
                    });
                    this.$('#isic-user-invite-submit').girderEnable(true);
                });
        },
        'click #isic-invitation-confirmation-invite-user': function (event) {
            this.confirmation = null;
            this.render();
            router.navigate('user/invite', {replace: true});
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
            this.$el.html(InvitationConfirmationPageTemplate({
                newUser: this.confirmation.newUser,
                inviteUrl: this.confirmation.inviteUrl
            }));
        } else {
            this.$el.html(InviteUserPageTemplate());
            this.$('#isic-user-invite-new-login').focus();
        }

        return this;
    }
});

export default InviteUserView;
