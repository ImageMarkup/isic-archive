/*globals d3*/

isic.views.ImagesViewSubViews = isic.views.ImagesViewSubViews || {};

isic.views.ImagesViewSubViews.DatasetPane = Backbone.View.extend({
    initialize: function () {
        this.listenTo(this.model, 'change:overviewHistogram', this.render);
        this.listenTo(this.model, 'change:filteredSetHistogram', this.render);
    },
    render: function () {
        var svg;

        if (!this.addedSvgElement) {
            this.$el.html(isic.templates.imageDatasetPage({
                title: 'Dataset'
            }));
            var histogramContainer = this.$('.isic-image-dataset-histogram-container');
            svg = d3.select(histogramContainer.get(0)).append('svg')
                .attr('class', 'content');
            this.histogram = new isic.views.ImagesViewSubViews.IndividualHistogram({
                el: svg.node(),
                model: this.model,
                attributeName: 'folderId',
                showCheckbox: true
            });
            this.addedSvgElement = true;
        } else {
            svg = d3.select(this.el).select('svg.content');
        }
        this.histogram.render();

        // Add special listeners to open a modal about each dataset
        var self = this;
        svg.select('.bins').selectAll('.bin')
            .on('click', _.bind(function (d) {
                var dataset = self.model.datasetCollection.find(function (dataset) {
                    return dataset.name() === d.label;
                });
                console.log('TODO: show a modal, describing the ' +
                    d + ' dataset (id: ' + dataset.id + ')');
            }, this));
        return this;
    }
});
