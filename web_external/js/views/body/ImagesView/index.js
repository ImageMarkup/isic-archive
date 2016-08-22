/*globals girder, jQuery, Image, recolorImageFilters*/

isic.views.ImagesSubViews = isic.views.ImagesSubViews || {};

isic.views.ImagesView = isic.View.extend({
    initialize: function () {
        var self = this;
        self.selectedImageId = null;

        // Initialize our subviews
        var params = {
            parentView: self
        };
        self.histogramPane = new isic.views.ImagesSubViews.HistogramPane(params);
        self.imageWall = new isic.views.ImagesSubViews.ImageWall(params);
        self.pagingPane = new isic.views.ImagesSubViews.PagingPane(params);
        self.imageDetailsPane = new isic.views.ImagesSubViews.ImageDetailsPane(params);

        window.onresize = function () {
            self.render();
        };
        self.attachListeners();
        self.updateCurrentPage();
    },
    attachListeners: function () {
        var self = this;
        self.listenTo(self.histogramPane, 'iv:changeFilters',
            function () {
                self.updateCurrentPage();
            });

        self.listenTo(self.imageWall, 'iv:selectImage',
            function (imageId) {
                self.selectedImageId = imageId;
                self.imageDetailsPane.updateDetails(imageId);
                self.render();
            });

        self.listenTo(self.imageDetailsPane, 'iv:deselectImage',
            function () {
                self.selectedImageId = null;
                self.imageWall.selectImage(null);
                self.render();
            });
    },
    updateCurrentPage: function () {
        var self = this;
        // TODO: pass in filters and paging settings
        // var filterString = self.histogramPane.getFilterString();
        girder.restRequest({
            path: 'image',
            data: {
                'limit': 50,
                'offset': 0
            }
        }).done(function (resp) {
            var newImageIds = resp.map(function (imageObj) {
                return imageObj._id;
            });
            self.imageWall.setImages(newImageIds);
            self.render();
        });
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

        if (self.selectedImageId) {
            self.$el.find('#isic-images-imageDetailsPane').css('display', '');
            self.imageDetailsPane.render();
        } else {
            self.$el.find('#isic-images-imageDetailsPane').css('display', 'none');
        }
        return self;
    }
});

isic.router.route('images', 'images', function (id) {
    girder.events.trigger('g:navigateTo', isic.views.ImagesView);
});
