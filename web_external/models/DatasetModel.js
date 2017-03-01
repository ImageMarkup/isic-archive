isic.models.DatasetModel = girder.Model.extend({
    resourceName: 'dataset',

    creator: function () {
        return new isic.models.UserModel(this.get('creator'));
    },

     /**
     * Create a new dataset from a .zip file of images.
     * @param [zipFileId] The ID of the .zip file.
     * @param [name] Name of the dataset.
     * @param [owner] Owner of the dataset.
     * @param [description] Description of the dataset.
     * @param [license] License of the dataset.
     * @param [signature] Signature of license agreement.
     * @param [anonymous] Whether to use an anonymous attribution for the dataset.
     * @param [attribution] Attribution of the dataset.
     */
    ingestImages: function (zipFileId, name, owner, description, license,
        signature, anonymous, attribution) {
        girder.restRequest({
            path: this.resourceName,
            type: 'POST',
            data: {
                zipFileId: zipFileId,
                name: name,
                owner: owner,
                description: description,
                license: license,
                signature: signature,
                anonymous: anonymous,
                attribution: attribution
            },
            error: null
        }).done(_.bind(function (resp) {
            this.set(resp);
            this.trigger('isic:ingestImages:success', resp);
        }, this)).error(_.bind(function (err) {
            this.trigger('isic:ingestImages:error', err);
        }, this));
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
            this.set(resp);
            this.trigger('isic:registerMetadata:success', resp);
        }, this)).error(_.bind(function (err) {
            this.trigger('isic:registerMetadata:error', err);
        }, this));
    },

     /**
     * Get the registered metadata for the dataset. Returns a promise.
     */
    getRegisteredMetadata: function () {
        var deferred = $.Deferred();
        girder.restRequest({
            path: this.resourceName + '/' + this.id + '/metadata'
        }).done(function (resp) {
            deferred.resolve(resp);
        });
        return deferred.promise();
    },

     /**
     * Apply registered metadata to the dataset. Returns a promise.
     * @param [metadataFileId] The ID of the metadata file.
     */
    applyMetadata: function (metadataFileId, save) {
        var deferred = $.Deferred();
        girder.restRequest({
            path: this.resourceName + '/' + this.id + '/metadata/' + metadataFileId,
            type: 'POST',
            data: {
                save: save
            },
            error: null
        }).done(function (resp) {
            deferred.resolve(resp);
        }).error(function (err) {
            deferred.reject(err);
        });
        return deferred.promise();
    }
});
