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
     * Check whether user is a a study administrator.
     *
     * Returns a promise that is resolved with a single boolean argument that
     * indicates whether the user is a study administrator.
     *
     */
    isAdministrator: function (user) {
        var deferred = $.Deferred();
        if (user) {
            var groups = new girder.collections.GroupCollection();
            groups.once('g:changed', function () {
                if (!groups.isEmpty()) {
                    var groupId = groups.first().id;
                    var userGroups = user.get('groups');
                    var studyAdmin = _.contains(userGroups, groupId);
                    deferred.resolve(studyAdmin);
                } else {
                    deferred.resolve(false);
                }
            }, this).once('g:error', function () {
                deferred.reject();
            }, this).fetch({
                text: 'Study Administrators',
                exact: true
            });
        } else {
            deferred.resolve(false);
        }
        return deferred.promise();
    }
});
