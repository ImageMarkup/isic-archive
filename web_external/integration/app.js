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

import GirderApp from 'girder/views/App';
import { getCurrentUser } from 'girder/auth';
import eventStream from 'girder/utilities/EventStream';
import FileCollection from 'girder/collections/FileCollection';
import FolderModel from 'girder/models/FolderModel';
import ItemModel from 'girder/models/ItemModel';
import {restRequest} from 'girder/rest';
import { splitRoute } from 'girder/misc';

import '../global.styl';
import LayoutHeaderView from './HeaderView';
import router from '../router';
import './routes';
import LayoutTemplate from '../layout/layout.pug';
import '../layout/layout.styl';

// The 'girder/rest' import will always overwrite the publicPath to Girder's static root, which we
// don't want; so re-overwrite it with the original value from the build configuration (which
// cannot be captured here at load-time, due to import hoisting)
__webpack_public_path__ = '/static/built/plugins/isic_archive/'; // eslint-disable-line no-undef, camelcase

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

        // this.footerView = new LayoutFooterView({
        //     el: this.$('#isic-app-footer-container'),
        //     parentView: this
        // });

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

/**
 * Patch ItemModel with a method to get the files within the item.
 */
ItemModel.prototype.getFiles = function () {
    restRequest({
        url: `${this.resourceName}/${this.id}/files`
    }).done((resp) => {
        let fileCollection = new FileCollection(resp);
        this.trigger('g:files', fileCollection);
    }).fail((err) => {
        this.trigger('g:error', err);
    });
};

/**
 * Patch FolderModel with a method to remove the contents of the
 * folder.
 */
FolderModel.prototype.removeContents = function () {
    restRequest({
        url: `${this.resourceName}/${this.id}/contents`,
        method: 'DELETE'
    }).done((resp) => {
        this.trigger('g:success');
    }).fail((err) => {
        this.trigger('g:error', err);
    });
};

export default IsicApp;
