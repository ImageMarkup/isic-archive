isic.views.ImagesFacetsPane = isic.View.extend({
    /**
     * @param {isic.collections.ImagesFacetCollection} settings.completeFacets
     * @param {isic.collections.ImagesFacetCollection} settings.filteredFacets
     * @param {isic.collections.ImagesFilters} settings.filters
     */
    initialize: function (settings) {
        this.completeFacets = settings.completeFacets;
        this.filteredFacets = settings.filteredFacets;
        this.filters = settings.filters;

        // TODO: Use the more general 'update' event, once Girder's version of Backbone is upgraded
        // TODO: ensure this fires when facets are modified in-place
        this.listenTo(this.completeFacets, 'sync', this.render);
    },

    render: function () {
        _.each(this.facetViews, function (facetView) {
            facetView.destroy();
        }, this);
        this.$el.empty();
        delete this.facetViews;

        this.facetViews = this.completeFacets.map(function (completeFacet) {
            var filteredFacet = this.filteredFacets.get(completeFacet.id);

            var FacetView = completeFacet.schema().FacetView;
            var facetView = new FacetView({
                completeFacet: completeFacet,
                filteredFacet: filteredFacet,
                filters: this.filters,
                parentView: this
            });

            this.$el.append(facetView.el);
            // Do not render until the view has been inserted into the main DOM
            facetView.render();

            return facetView;
        }, this);

        return this;
    }
});
