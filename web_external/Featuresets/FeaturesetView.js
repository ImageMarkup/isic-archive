isic.views.FeaturesetView = isic.View.extend({
    /**
     * @param {isic.models.FeaturesetModel} settings.model
     */
    initialize: function (settings) {
        // Display loading indicator
        this.loadingAnimation = new girder.views.LoadingAnimation({
            el: this.el,
            parentView: this
        }).render();

        this.model.once('g:fetched', function () {
            // Don't "this.loadingAnimation.destroy()", as it will unbind all events on "this.el"
            delete this.loadingAnimation;

            this.render();
        }, this).fetch();
    },

    render: function () {
        this.$el.html(isic.templates.featuresetPage({
            featureset: this.model
        }));

        return this;
    }
});
