isic.views.ImagesViewSubViews = isic.views.ImagesViewSubViews || {};

isic.views.ImagesViewSubViews.DatasetPane = isic.View.extend({
    initialize: function () {
        this.listenTo(this.model, 'change:overviewHistogram', this.render);
        this.listenTo(this.model, 'change:filteredSetHistogram', this.render);
    },
    render: function () {
        // Clean up any old IndividualHistogram sub-views (mostly for tooltips)
        if (this.histogram) {
            this.histogram.destroy();
            delete this.histogram;
        }

        this.$el.html('<div class="isic-image-dataset-histogram-container"></div>');
        var histogramContainer = this.$('.isic-image-dataset-histogram-container');
        this.histogram = new isic.views.ImagesViewSubViews.IndividualHistogram({
            el: histogramContainer,
            model: this.model,
            attributeName: 'folderId',
            title: 'Dataset',
            parentView: this
        }).render();

        return this;
    }
});
