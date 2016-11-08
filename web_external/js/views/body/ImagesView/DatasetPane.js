/*globals d3*/

isic.views.ImagesViewSubViews = isic.views.ImagesViewSubViews || {};

isic.views.ImagesViewSubViews.DatasetPane = Backbone.View.extend({
    initialize: function () {
        this.listenTo(this.model, 'change:overviewHistogram', this.render);
        this.listenTo(this.model, 'change:filteredSetHistogram', this.render);
    },
    render: function () {
        this.$el.html('<div class="isic-image-dataset-histogram-container"></div>');
        var histogramContainer = this.$('.isic-image-dataset-histogram-container');
        this.histogram = new isic.views.ImagesViewSubViews.IndividualHistogram({
            el: histogramContainer,
            model: this.model,
            attributeName: 'folderId',
            title: 'Dataset'
        }).render();

        return this;
    }
});
