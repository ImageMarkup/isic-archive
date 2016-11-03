isic.models.SegmentationModel = girder.Model.extend({
    resourceName: 'segmentation',

    creator: function() {
        return new isic.models.UserModel(this.get('creator'));
    }
});
