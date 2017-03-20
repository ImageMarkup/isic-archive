isic.models.SegmentationModel = isic.Model.extend({
    resourceName: 'segmentation',

    creator: function () {
        return new isic.models.UserModel(this.get('creator'));
    }
});
