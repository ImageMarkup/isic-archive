isic.models.UserModel = girder.models.UserModel.extend({
    name: function () {
        var name;
        if (this.has('firstName') && this.has('lastName')) {
            name = this.get('firstName') + ' ' + this.get('lastName') +
                ' (' + this.get('login') + ')';
        } else {
            name = this.get('login');
        }
        return name;
    },

    canCreateDataset: function () {
        return this.get('permissions').createDataset;
    },
    setCanCreateDataset: function (successCallback, failureCallback) {
        girder.restRequest({
            path: 'user/requestCreateDatasetPermission',
            type: 'POST'
        }).done(_.bind(function (resp) {
            if (_.has(resp, 'extra') && resp.extra === 'hasPermission') {
                // Directly update user permissions
                this.get('permissions').createDataset = true;
                this.trigger('change:permissions');
                successCallback(resp);
            } else {
                failureCallback(resp);
            }
        }, this));
    },
    canReviewDataset: function () {
        return this.get('permissions').reviewDataset;
    },
    getSegmentationSkill: function () {
        return this.get('permissions').segmentationSkill;
    },
    canAdminStudy: function () {
        return this.get('permissions').adminStudy;
    }
});
