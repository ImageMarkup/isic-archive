isic.models.FolderModel = girder.models.FolderModel.extend({
    /**
     * Remove the contents of the folder.
     */
    removeContents: function () {
        girder.restRequest({
            path: this.resourceName + '/' + this.id + '/contents',
            type: 'DELETE'
        }).done(_.bind(function (resp) {
            this.trigger('g:success');
        }, this)).error(_.bind(function (err) {
            this.trigger('g:error', err);
        }, this));
    }
});
