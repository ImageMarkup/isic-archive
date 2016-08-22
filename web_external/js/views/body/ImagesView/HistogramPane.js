/*globals girder, jQuery, Image*/

isic.views.ImagesSubViews = isic.views.ImagesSubViews || {};

isic.views.ImagesSubViews.HistogramPane = Backbone.View.extend({
    initialize: function (params) {
        var self = this;
        self.parentView = params.parentView;
    },
    render: function () {
        return this;
    }
});
