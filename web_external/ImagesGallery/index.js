isic.views.ImagesViewSubViews = isic.views.ImagesViewSubViews || {};

isic.views.ImagesView = isic.View.extend({
    initialize: function () {
        this.model = new isic.views.ImagesViewSubViews.ImagesViewModel();
        this.image = new isic.models.ImageModel();

        // Initialize our subviews
        this.facetsPane = new isic.views.ImagesFacetsPane({
            model: this.model,
            parentView: this
        });
        this.imageWall = new isic.views.ImagesViewSubViews.ImageWall({
            model: this.model,
            image: this.image,
            parentView: this
        });
        this.pagingPane = new isic.views.ImagesViewSubViews.PagingPane({
            model: this.model,
            parentView: this
        });
        this.imageDetailsPane = new isic.views.ImagesViewSubViews.ImageDetailsPane({
            image: this.image,
            parentView: this
        });

        $(window).on('resize.ImagesView', _.bind(this.render, this));

        this.listenTo(this.model.images, 'g:changed', function () {
            this.image.clear();
        });
        this.listenTo(this.image, 'change:_id', this.toggleDetailsPane);

        this.render();
    },
    destroy: function () {
        $(window).off('resize.ImagesView');

        isic.View.prototype.destroy.call(this);
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
            isic.shims.recolorImageFilters(['#00ABFF', '#444499', '#CCCCCC']);
            this.facetsPane.setElement(this.$('#isic-images-facetsPane'));
            this.imageWall.setElement(this.$('#isic-images-imageWall'));
            this.pagingPane.setElement(this.$('#isic-images-pagingPane'));
            this.imageDetailsPane.setElement(this.$('#isic-images-imageDetailsPane'));
            this.addedTemplate = true;
        }
        this.imageWall.render();
        this.pagingPane.render();
        this.facetsPane.render();
        this.imageDetailsPane.render();

        this.toggleDetailsPane();

        return this;
    }
});

isic.router.route('images', 'images', function () {
    var nextView = isic.views.ImagesView;
    if (!isic.views.TermsAcceptanceView.hasAcceptedTerms()) {
        nextView = isic.views.TermsAcceptanceView;
    }
    girder.events.trigger('g:navigateTo', nextView);
});
