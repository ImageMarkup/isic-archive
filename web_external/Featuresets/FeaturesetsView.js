import $ from 'jquery';

import LoadingAnimation from 'girder/views/widgets/LoadingAnimation';
import PaginateWidget from 'girder/views/widgets/PaginateWidget';

import FeaturesetCollection from '../collections/FeaturesetCollection';
import FeaturesetView from './FeaturesetView';
import View from '../view';

import ListingPageTemplate from '../common/Listing/listingPage.pug';
import '../common/Listing/listingPage.styl';

var FeaturesetsView = View.extend({
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

        this.featuresets = new FeaturesetCollection();
        this.listenTo(this.featuresets, 'g:changed', function () {
            this.loaded = true;
            this.render();
        });
        this.featuresets.fetch();

        // TODO: Use the more general 'update' event, once Girder's version of Backbone is upgraded
        this.listenTo(this.featuresets, 'remove', this.render);

        this.paginateWidget = new PaginateWidget({
            collection: this.featuresets,
            parentView: this
        });

        this.render();
    },

    render: function () {
        this.$el.html(ListingPageTemplate({
            title: 'Featuresets',
            models: this.featuresets.models,
            loaded: this.loaded
        }));

        this.paginateWidget.setElement(this.$('.isic-listing-paginate-container')).render();

        // Display loading indicator
        if (!this.loaded) {
            this.loadingAnimation = new LoadingAnimation({
                el: this.$('.isic-listing-loading-animation-container'),
                parentView: this
            }).render();
        } else {
            if (this.loadingAnimation) {
                this.loadingAnimation.destroy();
                delete this.loadingAnimation;
            }
        }

        return this;
    },

    renderFeatureset: function (index, container) {
        if (container.children().length === 0) {
            var featureset = this.featuresets.at(index);

            new FeaturesetView({ // eslint-disable-line no-new
                el: container,
                model: featureset,
                parentView: this
            });
        }
    }
});

export default FeaturesetsView;
