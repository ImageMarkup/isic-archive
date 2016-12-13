isic.models.DatasetModel = girder.Model.extend({
    resourceName: 'dataset',

    /**
     * Validate, add, or update dataset metadata.
     * @param [uploadFolderId] The ID of the folder that contains metadata.
     * @param [save] When true, save the metadata to the dataset if it passes
     *     validation. Otherwise, only validate the metadata.
     */
    validateMetadata: function (uploadFolderId, save) {
        girder.restRequest({
            path: this.resourceName + '/' + this.id + '/metadata',
            type: 'POST',
            data: {
                uploadFolderId: uploadFolderId,
                save: save
            }
        }).done(_.bind(function (resp) {
            this.trigger('isic:validated', resp);
        }, this)).error(_.bind(function (err) {
            this.trigger('g:error', err);
        }, this));
    }});
