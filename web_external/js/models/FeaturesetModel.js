isic.models.FeaturesetModel = girder.Model.extend({
    resourceName: 'featureset',

    /**
     * Get the name of the featureset.
     */
    name: function () {
        return this.get('name') + ' (version ' + this.get('version') + ')';
    },

    creator: function() {
        return new isic.models.UserModel(this.get('creator'));
    }
});
