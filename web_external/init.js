/*global isic:true*/

var isic = isic || {};

_.extend(isic, {
    models: {},
    collections: {},
    views: {},
    router: new Backbone.Router(),
    events: girder.events
});

girder.router.enabled(false);

Backbone.sync = function (method, model, options) {
    // In order to use the native "Backbone.Model.destroy" method (which triggers the correct
    // collection-level events, unlike the Girder version), a working "Backbone.sync" method is
    // required. Since all Ajax calls must be made via "girder.restRequest" (to add auth headers)
    // and since "Backbone.ajax" cannot be directly changed to use "girder.restRequest" (since
    // "girder.restRequest actually calls "Backbone.ajax"), "Backbone.sync" must be reimplemented to
    // use "girder.restRequest" directly.
    // In this reimplementation, the only important changes are:
    //   * Use "girder.restRequest" instead of "Backbone.ajax"
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
        // girder.restRequest expects a "path" option, and will set "url" internally
        params.path = _.result(model, 'url');
    }

    if (options.data == null && model && (method === 'create' || method === 'update' || method === 'patch')) {
        params.contentType = 'application/json';
        params.data = JSON.stringify(options.attrs || model.toJSON(options));
    }

    if (params.type !== 'GET') {
        params.processData = false;
    }

    var xhr = options.xhr = girder.restRequest(_.extend(params, options));
    model.trigger('request', model, xhr, options);
    return xhr;
};

/**
 * Patch girder.models.ItemModel with a method to get the files within the item.
 */
girder.models.ItemModel.prototype.getFiles = function () {
    girder.restRequest({
        path: this.resourceName + '/' + this.id + '/files'
    }).done(_.bind(function (resp) {
        var fileCollection = new girder.collections.FileCollection(resp);
        this.trigger('g:files', fileCollection);
    }, this)).fail(_.bind(function (err) {
        this.trigger('g:error', err);
    }, this));
};

/**
 * Patch girder.models.FolderModel with a method to remove the contents of the
 * folder.
 */
girder.models.FolderModel = girder.models.FolderModel.extend({
    removeContents: function () {
        girder.restRequest({
            path: this.resourceName + '/' + this.id + '/contents',
            type: 'DELETE'
        }).done(_.bind(function (resp) {
            this.trigger('g:success');
        }, this)).fail(_.bind(function (err) {
            this.trigger('g:error', err);
        }, this));
    }
});
