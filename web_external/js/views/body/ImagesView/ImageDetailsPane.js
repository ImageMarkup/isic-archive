/*globals girder, jQuery, Image*/

isic.views.ImagesSubViews = isic.views.ImagesSubViews || {};

isic.views.ImagesSubViews.ImageDetailsPane = Backbone.View.extend({
    initialize: function (params) {
        var self = this;
        self.parentView = params.parentView;
        self.details = {};
    },
    updateDetails: function () {
        // TODO: retrieve a larger version of the image,
        // as well as its metadata from the server
    },
    render: function () {
        var self = this;
        if (!self.addedDomListeners) {
            self.$el.find('.button').on('click',
            function () {
                self.trigger('iv:deselectImage');
            });
            self.addedDomListeners = true;
        }

        self.$el.find('pre').html(self.parentView.selectedImageId);
        return self;
    }
});
