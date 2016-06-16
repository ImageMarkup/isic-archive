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
    }
});
