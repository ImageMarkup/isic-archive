import _ from 'underscore';
import UAParser from 'ua-parser-js';

import View from '../view';

import BrowserAlertTemplate from './browserAlert.pug';
import './browserAlert.styl';

const BrowserAlertView = View.extend({
    className: 'isic-browser-alert',

    initialize: function (settings) {
        this.currentBrowserName = (new UAParser()).getBrowser().name;
        this.unsupportedBrowsers = [
            'Edge',
            'IE',
            'Safari'
        ];
    },

    render: function () {
        if (_.contains(this.unsupportedBrowsers, this.currentBrowserName)) {
            this.$el.html(BrowserAlertTemplate());
        }
        return this;
    }
});

export default BrowserAlertView;
