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

import './global.styl';
import LayoutFooterView from './layout/FooterView';
import LayoutHeaderView from './layout/HeaderView';
import router from './router';
import './routes';
import LayoutTemplate from './layout/layout.pug';
import './layout/layout.styl';

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

        return this;
    },

    navigateTo: function (View, settings, opts) {
        // TODO: Do we need this?
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
        var route = splitRoute(Backbone.history.fragment).base;
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

Backbone.sync = function (method, model, options) {
    // In order to use the native "Backbone.Model.destroy" method (which triggers the correct
    // collection-level events, unlike the Girder version), a working "Backbone.sync" method is
    // required. Since all Ajax calls must be made via "restRequest" (to add auth headers)
    // and since "Backbone.ajax" cannot be directly changed to use "restRequest" (since
    // "restRequest actually calls "Backbone.ajax"), "Backbone.sync" must be reimplemented to
    // use "restRequest" directly.
    // In this reimplementation, the only important changes are:
    //   * Use "restRequest" instead of "Backbone.ajax"
    //   * Set "params.path" instead of "params.url"
    var methodMap = {
        'create': 'POST',
        'update': 'PUT',
        'patch': 'PATCH',
        'delete': 'DELETE',
        'read': 'GET'
    };
    var type = methodMap[method];

    options = options || {};

    var params = {type: type, dataType: 'json'};

    if (!options.url) {
        // params.url = _.result(model, 'url') || urlError();
        // restRequest expects a "path" option, and will set "url" internally
        params.path = _.result(model, 'url');
    }

    if (options.data == null && model && (method === 'create' || method === 'update' || method === 'patch')) {
        params.contentType = 'application/json';
        params.data = JSON.stringify(options.attrs || model.toJSON(options));
    }

    if (params.type !== 'GET') {
        params.processData = false;
    }

    var xhr = options.xhr = restRequest(_.extend(params, options));
    model.trigger('request', model, xhr, options);
    return xhr;
};

/**
 * Patch ItemModel with a method to get the files within the item.
 */
ItemModel.prototype.getFiles = function () {
    restRequest({
        path: this.resourceName + '/' + this.id + '/files'
    }).done(_.bind(function (resp) {
        var fileCollection = new FileCollection(resp);
        this.trigger('g:files', fileCollection);
    }, this)).fail(_.bind(function (err) {
        this.trigger('g:error', err);
    }, this));
};

/**
 * Patch FolderModel with a method to remove the contents of the
 * folder.
 */
FolderModel.prototype.removeContents = function () {
    restRequest({
        path: this.resourceName + '/' + this.id + '/contents',
        type: 'DELETE'
    }).done(_.bind(function (resp) {
        this.trigger('g:success');
    }, this)).fail(_.bind(function (err) {
        this.trigger('g:error', err);
    }, this));
};

export default IsicApp;
