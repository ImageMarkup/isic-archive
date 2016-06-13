isic.models.DatasetModel = girder.Model.extend({
    resourceName: 'dataset',

    /**
     * Check whether user is a member of the dataset contributor group.
     *
     * The callback is called with a boolean argument. When true, the user is a
     * member of the dataset contributor group.
     *
     */
    userCanContribute: function (user, callback) {
        var groups = new girder.collections.GroupCollection();
        groups.once('g:changed', function () {
            if (!groups.isEmpty()) {
                var groupId = groups.first().id;
                var userGroups = girder.currentUser.get('groups');
                var datasetContributor = _.contains(userGroups, groupId);
                callback(datasetContributor);
            } else {
                callback(false);
            }
        }, this).once('g:error', function () {
            callback(false);
        }, this).fetch({
            text: 'Dataset Contributors',
            exact: true
        });
    }
});
