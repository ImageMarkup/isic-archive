/*globals d3*/

isic.views.ImagesViewSubViews = isic.views.ImagesViewSubViews || {};

isic.views.ImagesViewSubViews.ImageWall = isic.View.extend({
    initialize: function (settings) {
        this.image = settings.image;
        // For now we'll hard code this (and probably change it in the future),
        // depending on the page size
        this.imageSize = 128;

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
        d3.select(this.el)
          .selectAll('img')
          .remove();

        var sel = d3.select(this.el)
            .selectAll('img')
            .data(this.model.images.map(function (image) {
                return {
                    id: image.id,
                    name: image.get('name')
                };
            }));

        sel.enter()
            .append('img')
            .classed('thumb', true);

        sel.attr('src', _.bind(function (d) {
            return girder.apiRoot + '/image/' + d.id + '/thumbnail?width=' + this.imageSize;
        }, this))
            .attr('height', this.imageSize * 0.75)
            .attr('width', this.imageSize)
            .attr('data-toggle', 'tooltip')
            .attr('data-placement', 'auto')
            .attr('data-viewport', '#isic-images-imageWall')
            .classed('selected', _.bind(function (d) {
                return d.id === this.image.id;
            }, this))
            .on('click', _.bind(function (d) {
                this.clearTooltips();
                if (d3.event.shiftKey) {
                    new isic.views.ImageFullscreenWidget({ // eslint-disable-line no-new
                        el: $('#g-dialog-container'),
                        model: this.model.images.findWhere({_id: d.id}),
                        parentView: this
                    });
                } else {
                    this.selectImage(d.id === this.image.id ? null : d.id);
                }
            }, this))
            .each(function (d) {
                $(this).tooltip({
                    title: d.name
                });
            });
    }, 50),
    clearTooltips: function () {
        $('[data-toggle="tooltip"]').tooltip('hide');
    }
});
