isic.views.ImagesViewSubViews = isic.views.ImagesViewSubViews || {};

isic.views.ImagesView = isic.View.extend({
    initialize: function () {
        this.model = new isic.views.ImagesViewSubViews.ImagesViewModel();
        this.image = new isic.models.ImageModel();

        // Initialize our subviews
        var params = {
            model: this.model,
            parentView: this
        };
        this.datasetPane = new isic.views.ImagesViewSubViews.DatasetPane(params);
        this.histogramPane = new isic.views.ImagesViewSubViews.HistogramPane(params);
        this.imageWall = new isic.views.ImagesViewSubViews.ImageWall(
            _.extend(_.clone(params), {
                image: this.image
            }));
        this.pagingPane = new isic.views.ImagesViewSubViews.PagingPane(params);
        this.imageDetailsPane = new isic.views.ImagesViewSubViews.ImageDetailsPane({
            image: this.image,
            parentView: this
        });

        $(window).on('resize.ImagesView', _.bind(this.render, this));

        this.listenTo(this.model, 'change:imageIds', function () {
            this.image.clear();
        });
        this.listenTo(this.image, 'change:_id', this.selectedImageChanged);

        this.render();
    },
    destroy: function () {
        $(window).off('resize.ImagesView');

        isic.View.prototype.destroy.call(this);
    },
    selectedImageChanged: function () {
        if (this.image.id) {
            this.image.fetch();
        }
        this.toggleDetailsPane();
    },
    toggleDetailsPane: function () {
        if (this.image.id) {
            this.$('#isic-images-imageDetailsPane').css('display', '');
        } else {
            this.$('#isic-images-imageDetailsPane').css('display', 'none');
        }
    },
    render: function () {
        if (!(this.addedTemplate)) {
            this.$el.html(isic.templates.imagesPage({
                staticRoot: girder.staticRoot
            }));
            window.shims.recolorImageFilters(['#00ABFF', '#444499', '#CCCCCC']);
            this.datasetPane.setElement(this.$('#isic-images-datasetPane'));
            this.histogramPane.setElement(this.$('#isic-images-histogramPane'));
            this.imageWall.setElement(this.$('#isic-images-imageWall'));
            this.pagingPane.setElement(this.$('#isic-images-pagingPane'));
            this.imageDetailsPane.setElement(this.$('#isic-images-imageDetailsPane'));
            this.addedTemplate = true;
        }
        this.imageWall.render();
        this.pagingPane.render();
        this.datasetPane.render();
        this.histogramPane.render();
        this.imageDetailsPane.render();

        this.toggleDetailsPane();

        return this;
    }
});

isic.router.route('images', 'images', function (id) {
    girder.events.trigger('g:navigateTo', isic.views.ImagesView);
});
