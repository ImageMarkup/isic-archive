/*globals d3*/

isic.views.ImagesViewSubViews = isic.views.ImagesViewSubViews || {};

isic.views.ImagesViewSubViews.DatasetPane = Backbone.View.extend({
    events: {
        'click .toggle': function (evt) {
            this.$('.toggle').toggleClass('icon-down-open')
                .toggleClass('icon-right-open');

            this.$('svg.content').toggle();
        }
    },
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
                attributeName: 'folderId'
            });
            this.addedSvgElement = true;
        } else {
            svg = d3.select(this.el).select('svg.content');
        }
        this.histogram.render();

        return this;
    }
});
