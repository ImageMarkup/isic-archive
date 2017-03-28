isic.models.ImagesFacetModel = Backbone.Model.extend({
    schema: function () {
        return isic.FACET_SCHEMA[this.id];
    }
});

isic.collections.ImagesFacetCollection = Backbone.Collection.extend({
    model: isic.models.ImagesFacetModel,
    url: 'image/histogram',

    parse: function (resp, options) {
        // TODO: set this in a more formal way
        this.total = resp.__passedFilters__[0].count;

        return _.chain(resp)
            .omit('__passedFilters__')
            .map(function (facetBins, facetId) {
                return {
                    id: facetId,
                    bins: _.map(facetBins, function(facetBin) {
                        // Map a label of a null object to a "__null__" string because:
                        // * The null object cannot be stored on DOM elements as a data property
                        // * The null object will be coerced to a string of "null" in any places
                        //   it's used as the key to an object (e.g. ImagesFilters)
                        // * The server is eventually expecting "__null__" in filters, since a null
                        //   object cannot be serialized as a query string
                        // For all these reasons, it's best to just convert to "__null__" now for
                        // global consistency
                        // TODO: _.mapKeys from lodash would be handy
                        if (facetBin.label === null) {
                            facetBin = _.clone(facetBin);
                            facetBin.label = '__null__';
                        }
                        return facetBin;
                    })
                };
            })
            .value();
    }
});
