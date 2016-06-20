isic.views.FeaturesetView = isic.View.extend({
    initialize: function (settings) {
        this.featureset = new isic.models.FeaturesetModel({
            _id: settings.id
        }).once('g:fetched', function () {
            this.render();
        }, this).fetch();
    },

    render: function () {
        this.$el.html(isic.templates.featuresetPage({
            featureset: this.featureset,
            stringify: this._stringify
        }));

        return this;
    },

    _stringify: function (val) {
        return JSON.stringify(val, null, 4);
    }
});
