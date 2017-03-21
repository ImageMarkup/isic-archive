isic.models.FeaturesetModel = isic.Model.extend({
    resourceName: 'featureset',

    /**
     * Get the name of the featureset.
     */
    name: function () {
        return this.get('name') + ' (version ' + this.get('version') + ')';
    },

    creator: function () {
        return new isic.models.UserModel(this.get('creator'));
    },

    destroy: function (options) {
        var params = _.clone(options);
        // Featureset deletion may fail if it's being used by a study
        params.wait = true;

        return isic.Model.prototype.destroy.call(this, params);
    }
});
