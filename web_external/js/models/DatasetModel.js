isic.models.DatasetModel = girder.Model.extend({
    resourceName: 'dataset',

    /**
     * Check whether user is a member of the dataset contributor group.
     *
     * Returns a promise that is resolved with a single boolean argument that
     * indicates whether the user is a member of the dataset contributor group.
     *
     */
    userCanContribute: function (user) {
        var deferred = $.Deferred();
        if (user) {
            var groups = new girder.collections.GroupCollection();
            groups.once('g:changed', function () {
                if (!groups.isEmpty()) {
                    var groupId = groups.first().id;
                    var userGroups = user.get('groups');
                    var datasetContributor = _.contains(userGroups, groupId);
                    deferred.resolve(datasetContributor);
                } else {
                    deferred.resolve(false);
                }
            }, this).once('g:error', function () {
                deferred.reject();
            }, this).fetch({
                text: 'Dataset Contributors',
                exact: true
            });
        } else {
            deferred.resolve(false);
        }
        return deferred.promise();
    }
});
