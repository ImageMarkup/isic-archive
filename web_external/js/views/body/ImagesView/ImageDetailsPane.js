/*globals girder, jQuery, Image*/

isic.views.ImagesSubViews = isic.views.ImagesSubViews || {};

isic.views.ImagesSubViews.ImageDetailsPane = Backbone.View.extend({
    initialize: function () {
        var self = this;
        self.listenTo(self.model, 'change:selectedImageId', this.render);
    },
    render: function () {
        var self = this;
        if (!self.addedDomListeners) {
            self.$el.find('.button').on('click',
                function () {
                    self.model.set('selectedImageId', null);
                });
            self.addedDomListeners = true;
        }

        self.$el.find('pre').html(self.model.get('selectedImageId'));
        return self;
    }
});
