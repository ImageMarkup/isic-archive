/*globals d3*/

// For now we'll hard code this (and probably change it in the future),
// depending on the page size
var imageSize = 128;

isic.views.ImagesViewSubViews = isic.views.ImagesViewSubViews || {};

isic.views.ImagesViewSubViews.ImageWall = Backbone.View.extend({
    initialize: function (settings) {
        this.image = settings.image;
        this.imageCache = {};
        this.loadedImages = {};
        this.imageColumnLookup = {};
        this.imageColumns = [];

        this.listenTo(this.image, 'change:_id', this.render);
        this.listenTo(this.model, 'change:imageIds', this.render);
    },
    selectImage: function (imageId) {
        if (imageId !== null) {
            this.image.set('_id', imageId);
        } else {
            this.image.clear();
        }
    },
    render: _.debounce(function () {
        var sel = d3.select(this.el)
            .selectAll('img')
            .data(this.model.get('imageIds'));

        sel.enter()
            .append('img')
            .classed('thumb', true);

        sel.attr('src', function (d) {
            return girder.apiRoot + '/image/' + d + '/thumbnail?width=128';
        })
            .attr('height', 96)
            .attr('width', 128)
            .classed('selected', _.bind(function (d) {
                return d === this.image.id;
            }, this))
            .on('click', _.bind(function (d) {
                this.selectImage(d === this.image.id ? null : d)
            }, this));
    }, 50)
});
