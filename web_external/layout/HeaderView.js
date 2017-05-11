import $ from 'jquery';

import {getCurrentUser} from 'girder/auth';
import events from 'girder/events';

import LayoutHeaderUserView from './HeaderUserView';
import View from '../view';

import LayoutHeaderTemplate from './layoutHeader.pug';
import './layoutHeader.styl';

var LayoutHeaderView = View.extend({
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

        // Specify trigger for tooltip to ensure that tooltip hides when button
        // is clicked. See http://stackoverflow.com/a/33585981/2522042.
        this.$('a[title]').tooltip({
            placement: 'bottom',
            trigger: 'hover',
            delay: {show: 300}
        });

        new LayoutHeaderUserView({
            el: this.$('.isic-current-user-wrapper'),
            parentView: this
        }).render();
    }
});

export default LayoutHeaderView;
