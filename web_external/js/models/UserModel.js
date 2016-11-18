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
    setCanCreateDataset: function () {
        this.get('permissions').createDataset = true;
        this.trigger('change:permissions');
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
