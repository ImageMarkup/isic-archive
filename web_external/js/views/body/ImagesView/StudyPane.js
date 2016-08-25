/*globals d3*/

isic.views.ImagesViewSubViews = isic.views.ImagesViewSubViews || {};

isic.views.ImagesViewSubViews.StudyPane = Backbone.View.extend({
    initialize: function () {
        var self = this;

        self.listenTo(self.model, 'change:overviewHistogram', self.render);
        self.listenTo(self.model, 'change:filteredSetHistogram', self.render);
        self.listenTo(self.model, 'change:pageHistogram', self.render);
    },
    render: function () {
        var self = this;
        var svg;

        if (!self.addedSvgElement) {
            var svg = d3.select(self.el).append('svg')
                .attr('class', 'content');
            self.histogram = new isic.views.ImagesViewSubViews.IndividualHistogram({
                el: svg.node(),
                model: self.model,
                attributeName: 'folderId'
            });
            self.addedSvgElement = true;
        } else {
            self.histogram.render();
            // TODO: add special icons / listeners to each label
        }
        return this;
    }
});
