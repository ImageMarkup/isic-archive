isic.models.UserModel = girder.models.UserModel.extend({
    canCreateDataset: function () {
        return this.get('permissions').createDataset;
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
