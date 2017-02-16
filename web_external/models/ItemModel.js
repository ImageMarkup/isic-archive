isic.models.ItemModel = girder.models.ItemModel.extend({
    /**
     * Get the files within the item.
     */
    getFiles: function () {
        girder.restRequest({
            path: this.resourceName + '/' + this.id + '/files'
        }).done(_.bind(function (resp) {
            var fileCollection = new girder.collections.FileCollection(resp);
            this.trigger('g:files', fileCollection);
        }, this)).error(_.bind(function (err) {
            this.trigger('g:error', err);
        }, this));
    }
});
