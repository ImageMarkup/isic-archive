/*globals d3*/

isic.views.ImagesViewSubViews = isic.views.ImagesViewSubViews || {};

isic.views.ImagesViewSubViews.ImageWall = isic.View.extend({
    /**
     * @param {isic.views.ImagesViewSubViews.ImagesViewModel} settings.model
     * @param {isic.models.ImageModel} settings.image
     */
    initialize: function (settings) {
        this.image = settings.image;
        // For now we'll hard code this (and probably change it in the future),
        // depending on the page size
        this.imageSize = 128;

        this.listenTo(this.model.images, 'g:changed', this.render);
    },
    render: _.debounce(function () {
        var self = this;

        // Since tooltip-enabled elements are about to be destroyed, first
        // remove any active tooltips from them.
        this.clearTooltips();
        // Ordinarily, we would use the exit selection to clean up after
        // ourselves, but deleting all the img elements has the effect of
        // visually "streaming in" the new data, rather than updating the old
        // images, which feels error-prone.
        d3.select(this.el)
          .selectAll('img')
          .remove();

        d3.select(this.el)
            .selectAll('img')
            .data(this.model.images.map(function (image) {
                return {
                    id: image.id,
                    name: image.get('name')
                };
            }))
            .enter()
            .append('img')
            .classed('thumb', true)
            .attr('src', _.bind(function (d) {
                return girder.apiRoot + '/image/' + d.id + '/thumbnail?width=' + this.imageSize;
            }, this))
            .attr('height', this.imageSize * 0.75)
            .attr('width', this.imageSize)
            .on('click', function (d) {
                self.clearTooltips();
                if (d3.event.shiftKey) {
                    new isic.views.ImageFullscreenWidget({ // eslint-disable-line no-new
                        el: $('#g-dialog-container'),
                        model: self.model.images.findWhere({_id: d.id}),
                        parentView: self
                    }).render();
                } else {
                    // Clear 'selected' class from all elements.
                    d3.select(self.el)
                        .selectAll('img')
                        .classed('selected', false);

                    if (d.id === self.image.id) {
                        self.image.clear();
                    } else {
                        d3.select(this)
                            .classed('selected', true);

                        self.image.clear({silent: true});
                        self.image.set('_id', d.id);
                        self.image.fetch();
                    }
                }
            })
            .attr('data-toggle', 'tooltip')
            .each(function (d) {
                $(this).tooltip({
                    title: d.name,
                    placement: 'auto',
                    viewport: '#isic-images-imageWall',
                    trigger: 'hover'
                });
            });
    }, 50),
    clearTooltips: function () {
        this.$('[data-toggle="tooltip"]').tooltip('hide');
        // For unknown reasons, tooltips sometimes remain after they've been
        // hidden, so manually destroy the tooltip element.
        this.$('.tooltip').remove();
    }
});
