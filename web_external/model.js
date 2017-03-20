isic.Model = girder.Model.extend({
    urlRoot: function () {
        return this.resourceName;
    }
});
