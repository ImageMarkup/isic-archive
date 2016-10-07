/*globals d3*/

// For now we'll hard code this (and probably change it in the future),
// depending on the page size
var imageSize = 128;

isic.views.ImagesViewSubViews = isic.views.ImagesViewSubViews || {};

isic.views.ImagesViewSubViews.ImageWall = isic.View.extend({
    initialize: function (settings) {
        this.image = settings.image;
        this.imageCache = {};
        this.loadedImages = {};
        this.imageColumnLookup = {};
        this.imageColumns = [];

        this.listenTo(this.image, 'change:_id', this.render);
        this.listenTo(this.model.images, 'g:changed', this.render);
    },
    selectImage: function (imageId) {
        if (imageId !== null) {
            this.image.set('_id', imageId);
        } else {
            this.image.clear();
        }
    },
    render: _.debounce(function () {
        var self = this;

        d3.select(this.el)
          .selectAll('img')
          .remove();

        var sel = d3.select(this.el)
            .selectAll('img')
            .data(this.model.images.pluck('_id'));

        sel.enter()
            .append('img')
            .classed('thumb', true);

        sel.attr('src', function (d) {
            return girder.apiRoot + '/image/' + d + '/thumbnail?width=' + imageSize;
        })
            .attr('height', imageSize * 0.75)
            .attr('width', imageSize)
            .attr('data-toggle', 'tooltip')
            .attr('data-placement', 'auto')
            .attr('data-viewport', '#isic-images-imageWall')
            .classed('selected', _.bind(function (d) {
                return d === this.image.id;
            }, this))
            .on('click', _.bind(function (d) {
                this.clearTooltips();
                if (d3.event.shiftKey) {
                    var image = new isic.models.ImageModel({
                        _id: d
                    });
                    new isic.views.ImageFullscreenWidget({ // eslint-disable-line no-new
                        el: $('#g-dialog-container'),
                        model: image,
                        parentView: this
                    });
                } else {
                    this.selectImage(d === this.image.id ? null : d);
                }
            }, this))
            .each(function (d) {
                var imageCollection = self.model.images;
                var imageModel = imageCollection.find(function (x) { return x.id === d; });

                $(this).tooltip({
                    title: imageModel.get('name')
                });
            });
    }, 50),
    clearTooltips: function () {
        $('[data-toggle="tooltip"]').tooltip('hide');
    }
});
