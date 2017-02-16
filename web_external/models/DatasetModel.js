isic.models.DatasetModel = girder.Model.extend({
    resourceName: 'dataset',

    creator: function () {
        return new isic.models.UserModel(this.get('creator'));
    },

     /**
     * Register a metadata file with the dataset.
     * @param [metadataFileId] The ID of the metadata file.
     */
    registerMetadata: function (metadataFileId) {
        girder.restRequest({
            path: this.resourceName + '/' + this.id + '/metadata',
            type: 'POST',
            data: {
                metadataFileId: metadataFileId
            },
            error: null
        }).done(_.bind(function (resp) {
            this.trigger('isic:registerMetadata:success', resp);
        }, this)).error(_.bind(function (err) {
            this.trigger('isic:registerMetadata:error', err);
        }, this));
    }
});
