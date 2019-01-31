import {getCurrentUser, logout} from '@girder/core/auth';
import events from '@girder/core/events';

import 'girder_plugins/gravatar/models/UserModel';

import router from '../router';
import View from '../view';

import LayoutHeaderUserTemplate from './layoutHeaderUser.pug';
import './layoutHeaderUser.styl';
import './layoutHeader.styl';

const LayoutHeaderUserView = View.extend({
    events: {
        'click a.g-login': function () {
            events.trigger('g:loginUi');
        },

        'click a.g-register': function () {
            events.trigger('g:registerUi');
        },

        'click a.g-logout': logout,

        'click a.g-my-settings': function () {
            router.navigate(`useraccount/${getCurrentUser().id}/info`, {trigger: true});
        }
    },

    render: function () {
        let currentUser = getCurrentUser();
        this.$el.html(LayoutHeaderUserTemplate({
            currentUser: currentUser
        }));

        if (currentUser) {
            this.$('.isic-portrait-wrapper').css(
                'background-image', `url(${currentUser.getGravatarUrl(36)})`);
        }
        return this;
    }
});

export default LayoutHeaderUserView;
