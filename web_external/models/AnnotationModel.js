isic.models.AnnotationModel = girder.Model.extend({
    resourceName: 'annotation',

    isComplete: function () {
        return this.get('state') === 'complete';
    },

    image: function () {
        return new isic.models.ImageModel(this.get('image'));
    }
});
