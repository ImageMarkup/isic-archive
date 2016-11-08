isic.models.StudyModel = girder.Model.extend({
    resourceName: 'study',

    /**
     * Add a user to the study.
     */
    addUser: function (userId) {
        girder.restRequest({
            path: this.resourceName + '/' + this.get('_id') + '/user',
            type: 'POST',
            data: {
                userId: userId
            }
        }).done(_.bind(function (resp) {
            this.trigger('g:addedUser');
        }, this)).error(_.bind(function (err) {
            this.trigger('g:error', err);
        }, this));
    },

    /**
     * Return the featureset for this study.
     *
     * This returns a FeaturesetModel with only a few summary properties of
     * the featureset. To retrieve all properties of the featureset, call
     * ".fetch()" on the FeaturesetModel.
     */
    featureset: function () {
        return new isic.models.FeaturesetModel(this.get('featureset'));
    }
});
