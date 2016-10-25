isic.views.FeaturesetsView = isic.View.extend({
    // TODO refactor
    events: {
        'show.bs.collapse .isic-listing-panel-collapse': function (event) {
            var target = $(event.target);
            target.parent().find('.icon-right-open').removeClass('icon-right-open').addClass('icon-down-open');

            var viewIndex = parseInt(target.attr('data-model-index'), 10);
            var viewContainer = target.find('.isic-listing-panel-body');
            this.renderFeatureset(viewIndex, viewContainer);
        },
        'hide.bs.collapse .isic-listing-panel-collapse': function (event) {
            $(event.target).parent().find('.icon-down-open').removeClass('icon-down-open').addClass('icon-right-open');
        }
    },

    initialize: function (settings) {
        this.loaded = false;

        this.featuresets = new isic.collections.FeaturesetCollection();
        this.featuresets.once('g:changed', function () {
            this.loaded = true;
            this.render();
        }, this).fetch();

        this.render();
    },

    render: function () {
        this.$el.html(isic.templates.featuresetsPage({
            title: 'Featuresets',
            models: this.featuresets.models,
            loaded: this.loaded,
            formatFeatureset: this.formatFeatureset
        }));

        // Display loading indicator
        if (!this.loaded) {
            new girder.views.LoadingAnimation({
                el: this.$('.isic-listing-loading-animation-container'),
                parentView: this
            }).render();
        }

        return this;
    },

    renderFeatureset: function (index, container) {
        if (container.children().length === 0) {
            var featuresetId = this.featuresets.at(index).id;

            // Display loading indicator
            new girder.views.LoadingAnimation({
                el: container,
                parentView: this
            }).render();

            new isic.views.FeaturesetView({ // eslint-disable-line no-new
                el: container,
                id: featuresetId,
                parentView: this
            });
        }
    }
});

isic.router.route('featuresets', 'featuresets', function (id) {
    girder.events.trigger('g:navigateTo', isic.views.FeaturesetsView);
});
