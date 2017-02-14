isic.models.DatasetModel = girder.Model.extend({
    resourceName: 'dataset',

    creator: function () {
        return new isic.models.UserModel(this.get('creator'));
    }
});
