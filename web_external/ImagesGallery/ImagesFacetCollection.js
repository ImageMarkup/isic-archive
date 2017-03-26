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
            .map(function (value, key) {
                return {
                    id: key,
                    bins: value
                };
            })
            .value();
    }
});
