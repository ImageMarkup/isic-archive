/*globals girder, jQuery, d3, Image*/

isic.views.ImagesSubViews = isic.views.ImagesSubViews || {};

isic.views.ImagesSubViews.PagingPane = Backbone.View.extend({
    initialize: function () {
        var self = this;
        self.listenTo(self.model, 'change:imageIds', self.render);
    },
    render: function () {
        var self = this;
        if (!self.addedImages) {
            d3.select(this.el).selectAll('.button')
                .append('img')
                .attr('src', function () {
                    var imgName = this.parentNode.getAttribute('id').slice(12);
                    return girder.staticRoot +
                    '/built/plugins/isic_archive/extra/img/' +
                    imgName + '.svg';
                });
            self.addedImages = true;
        }
    }
});
