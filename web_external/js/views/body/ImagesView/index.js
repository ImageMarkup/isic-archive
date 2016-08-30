isic.views.ImagesViewSubViews = isic.views.ImagesViewSubViews || {};

isic.views.ImagesView = isic.View.extend({
    initialize: function () {
        var self = this;
        self.model = new isic.views.ImagesViewSubViews.ImagesViewModel();

        // Initialize our subviews
        var params = {
            model: self.model,
            parentView: this
        };
        self.studyPane = new isic.views.ImagesViewSubViews.StudyPane(params);
        self.histogramPane = new isic.views.ImagesViewSubViews.HistogramPane(params);
        self.imageWall = new isic.views.ImagesViewSubViews.ImageWall(params);
        self.pagingPane = new isic.views.ImagesViewSubViews.PagingPane(params);
        self.imageDetailsPane = new isic.views.ImagesViewSubViews.ImageDetailsPane(params);

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
            window.shims.recolorImageFilters(['#00ABFF', '#444499', '#CCCCCC']);
            self.studyPane.setElement(self.$el.find('#isic-images-studyPane')[0]);
            self.histogramPane.setElement(self.$el.find('#isic-images-histogramPane')[0]);
            self.imageWall.setElement(self.$el.find('#isic-images-imageWall')[0]);
            self.pagingPane.setElement(self.$el.find('#isic-images-pagingPane')[0]);
            self.imageDetailsPane.setElement(self.$el.find('#isic-images-imageDetailsPane')[0]);
            self.addedTemplate = true;
        }
        self.imageWall.render();
        self.pagingPane.render();
        self.studyPane.render();
        self.histogramPane.render();
        self.imageDetailsPane.render();

        self.toggleDetailsPane();

        return this;
    }
});

isic.router.route('images', 'images', function (id) {
    girder.events.trigger('g:navigateTo', isic.views.ImagesView);
});
