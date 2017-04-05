isic.models.StudyModel = isic.Model.extend({
    resourceName: 'study',

    creator: function () {
        return new isic.models.UserModel(this.get('creator'));
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
    },

    users: function () {
        var userModels = this.get('users').map(function (user) {
            return new isic.models.UserModel(user);
        });
        return new isic.collections.UserCollection(userModels);
    },

    /**
     * Add a user to the study.
     */
    addUser: function (userId) {
        // TODO: return a promise here, and use it (rather than events)
        girder.restRequest({
            path: this.resourceName + '/' + this.id + '/users',
            type: 'POST',
            data: {
                userIds: JSON.stringify([userId])
            }
        }).done(_.bind(function (resp) {
            this.trigger('g:addedUser');
        }, this)).fail(_.bind(function (err) {
            this.trigger('g:error', err);
        }, this));
    },

    removeUser: function (user) {
        return girder.restRequest({
            path: this.resourceName + '/' + this.id + '/users/' + user.id,
            type: 'DELETE',
            error: null
        });
        // TODO: update the model in-place here, with the new list of annotators,
        // then trigger a changed event
    },

    destroy: function (options) {
        // Don't modify the "options", but override some properties
        var params = _.clone(options);
        // Study deletion may fail if it has completed annotations
        params.wait = true;

        return isic.Model.prototype.destroy.call(this, params);
    }
});
