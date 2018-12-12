import $ from 'jquery';

import {getCurrentUser} from 'girder/auth';
import events from 'girder/events';

import LayoutHeaderUserView from './HeaderUserView';
import View from '../view';

import LayoutHeaderTemplate from './layoutHeader.pug';
import './layoutHeader.styl';

const LayoutHeaderView = View.extend({
    events: {
        'mouseenter .dropdown': function (event) {
            $(event.currentTarget).addClass('open');
        },
        'mouseleave .dropdown': function (event) {
            $(event.currentTarget).removeClass('open');
        },
        'click .dropdown': function (event) {
            $(event.currentTarget).removeClass('open');
        }
    },

    initialize: function (settings) {
        this.render();

        this.listenTo(events, 'g:login g:login-changed', this.render);
    },

    render: function () {
        this.$el.html(LayoutHeaderTemplate({
            currentUser: getCurrentUser()
        }));

        new LayoutHeaderUserView({
            el: this.$('.isic-current-user-wrapper'),
            parentView: this
        }).render();

        return this;
    }
});

export default LayoutHeaderView;
