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
