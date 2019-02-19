import Backbone from 'backbone';
import $ from 'jquery';
import 'bootstrap/dist/css/bootstrap.css';
// TODO: Move these bootstrap JS plugins to where they're actually used
import 'bootstrap/js/collapse';
import 'bootstrap/js/dropdown';
import 'bootstrap/js/modal';
// Bootstrap tooltip is a requirement of popover
import 'bootstrap/js/tooltip';
import 'bootstrap/js/popover';
import 'bootstrap/js/tab';
import 'bootstrap/js/transition';
// Import select2 for side effects, registering it as a jQuery plugin
import 'select2';
import 'select2/dist/css/select2.css';
import 'select2-bootstrap-theme/dist/select2-bootstrap.css';
import _ from 'underscore';

import GirderApp from '@girder/core/views/App';
import { getCurrentUser } from '@girder/core/auth';
import eventStream from '@girder/core/utilities/EventStream';
import { splitRoute } from '@girder/core/misc';

import './global.styl';
import LayoutFooterView from './layout/FooterView';
import LayoutHeaderView from './layout/HeaderView';
import router from './router';
import './routes';
import LayoutTemplate from './layout/layout.pug';
import './layout/layout.styl';
import BrowserAlertView from './layout/BrowserAlertView';

const IsicApp = GirderApp.extend({
    start: function () {
        // Set select2 default options
        $.fn.select2.defaults.set('theme', 'bootstrap');

        return GirderApp.prototype.start.apply(this, arguments);
    },

    bindGirderEvents: function () {
        // This might be overridden in the near future
        GirderApp.prototype.bindGirderEvents.apply(this, arguments);
    },

    _createLayout: function () {
        // Prevent the default behavior
    },

    render: function () {
        if (!this._started) {
            return;
        }

        this.$el.html(LayoutTemplate());

        this.headerView = new LayoutHeaderView({
            el: this.$('#isic-app-header-container'),
            parentView: this
        });

        this.footerView = new LayoutFooterView({
            el: this.$('#isic-app-footer-container'),
            parentView: this
        });

        this.browserAlert = new BrowserAlertView({
            parentView: this
        });

        return this;
    },

    navigateTo: function (View, settings, opts) {
        // This may be added by top-level views' "render" methods
        this.$('#g-app-body-container').removeClass('isic-body-nopad');

        settings = settings || {};
        opts = opts || {};

        if (View) {
            if (this.bodyView) {
                this.bodyView.destroy();
            }

            settings = _.extend(settings, {
                el: this.$('#g-app-body-container'),
                parentView: this
            });

            /* We let the view be created in this way even though it is
             * normally against convention.
             */
            this.bodyView = new View(settings);

            if (opts.renderNow) {
                this.bodyView.render();
            }

            this.browserAlert
                .render()
                .$el.prependTo(this.bodyView.$el);
        } else {
            console.error('Undefined page.');
        }
        return this;
    },

    login: function () {
        // Re-implement this, to use ISIC's instance of the router
        // TODO: if the router were stored as an App instance property, this wouldn't be necessary
        let route = splitRoute(Backbone.history.fragment).base;
        Backbone.history.fragment = null;
        eventStream.close();

        if (getCurrentUser()) {
            eventStream.open();
            router.navigate(route, {trigger: true});
        } else {
            router.navigate('/', {trigger: true});
        }
    }
});

export default IsicApp;
