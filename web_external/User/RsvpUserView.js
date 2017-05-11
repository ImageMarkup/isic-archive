import _ from 'underscore';

import View from '../view';
import router from '../router';
import {showAlertDialog} from '../common/utilities';

import RsvpUserPageTemplate from './rsvpUserPage.pug';
import './rsvpUserPage.styl';

var RsvpUserView = View.extend({
    events: {
        'submit #isic-user-rsvp-form': function (event) {
            event.preventDefault();
            this.$('#isic-user-rsvp-submit').prop('disabled', true);

            if (this.$('#isic-user-rsvp-password').val() !== this.$('#isic-user-rsvp-password2').val()) {
                showAlertDialog({
                    text: 'Passwords do not match, try again.',
                    callback: _.bind(function () {
                        this.$('#isic-user-rsvp-password2').val('').focus();
                    }, this)
                });
                this.$('#isic-user-rsvp-submit').prop('disabled', false);
                return;
            }

            this.user
                .changePassword(
                    this.token,
                    this.$('#isic-user-rsvp-password').val()
                )
                .done(function () {
                    router.navigate('tasks', {trigger: true});
                })
                .fail(_.bind(function (resp) {
                    showAlertDialog({
                        text: '<h4>Error changing password</h4><br>' + _.escape(resp.responseJSON.message),
                        escapedHtml: true
                    });
                    this.$('#isic-user-rsvp-submit').prop('disabled', false);
                }, this));
        }
    },

    /**
     * @param {UserModel} settings.user - The user to complete registration for.
     * @param {string} settings.token - The TEMPORARY_USER_AUTH token.
     */
    initialize: function (settings) {
        this.user = settings.user;
        this.token = settings.token;

        this.render();
    },

    render: function () {
        this.$el.html(RsvpUserPageTemplate({
            user: this.user
        }));

        this.$('#isic-user-rsvp-password').focus();

        return this;
    }
});

export default RsvpUserView;
