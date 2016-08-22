/*globals girder, jQuery, Image, recolorImageFilters*/

isic.views.ImagesSubViews = isic.views.ImagesSubViews || {};

isic.views.ImagesView = isic.View.extend({
    initialize: function () {
        var self = this;
        self.model = new isic.views.ImagesViewModel();

        // Initialize our subviews
        var params = {
            model: self.model
        };
        self.histogramPane = new isic.views.ImagesSubViews.HistogramPane(params);
        self.imageWall = new isic.views.ImagesSubViews.ImageWall(params);
        self.pagingPane = new isic.views.ImagesSubViews.PagingPane(params);
        self.imageDetailsPane = new isic.views.ImagesSubViews.ImageDetailsPane(params);

        window.onresize = function () {
            self.render();
        };
        self.listenTo(self.model, 'change:selectedImageId', self.toggleDetailsPane);

        self.render();
    },
    toggleDetailsPane: function () {
        var self = this;
        if (self.model.get('selectedImageId') !== null) {
            self.$el.find('#isic-images-imageDetailsPane').css('display', '');
        } else {
            self.$el.find('#isic-images-imageDetailsPane').css('display', 'none');
        }
    },
    render: function () {
        var self = this;
        if (!(self.addedTemplate)) {
            self.$el.html(isic.templates.imagesPage({
                staticRoot: girder.staticRoot
            }));
            recolorImageFilters(['#00ABFF', '#444499']);
            self.histogramPane.setElement(self.$el.find('#isic-images-histogramPane')[0]);
            self.imageWall.setElement(self.$el.find('#isic-images-imageWall')[0]);
            self.pagingPane.setElement(self.$el.find('#isic-images-pagingPane')[0]);
            self.imageDetailsPane.setElement(self.$el.find('#isic-images-imageDetailsPane')[0]);
            self.addedTemplate = true;
        }
        self.imageWall.render();
        self.pagingPane.render();
        self.histogramPane.render();
        self.imageDetailsPane.render();

        self.toggleDetailsPane();
    }
});

isic.router.route('images', 'images', function (id) {
    girder.events.trigger('g:navigateTo', isic.views.ImagesView);
});
