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
            svg = d3.select(self.el).append('svg')
                .attr('class', 'content');
            self.histogram = new isic.views.ImagesViewSubViews.IndividualHistogram({
                el: svg.node(),
                model: self.model,
                attributeName: 'folderId'
            });
            self.addedSvgElement = true;
        } else {
            svg = d3.select(self.el).select('svg.content');
        }
        self.histogram.render();

        // Add special listeners to open a modal about each study
        svg.select('.bins').selectAll('.bin')
            .on('click', function (d) {
                console.log('TODO: show a modal, describing the ' +
                    d + ' study (folder id: ' + self.model.studyIdLookup[d] + ')');
            });
        return this;
    }
});
