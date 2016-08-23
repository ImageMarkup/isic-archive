isic.views.ImagesViewSubViews = isic.views.ImagesViewSubViews || {};

isic.views.ImagesViewSubViews.IndividualHistogram = Backbone.View.extend({
    render: function () {
        d3.select(this.el).append('text')
            .attr({
                x: 10,
                y: 50
            }).text('an individual histogram will render here!');
        return this;
    }
});
