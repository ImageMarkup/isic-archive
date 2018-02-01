import _ from 'underscore';

import View from '../../view';
import {MultiselectableFeatureCollection} from '../../collections/FeatureCollection';

import ImagesFacetsPaneTemplate from './imagesFacetsPane.pug';
import './imagesFacetsPane.styl';

import FeatureFacetsSubsectionTemplate from './featureFacetsSubsection.pug';
import FeatureFacetTemplate from './featureFacet.pug';
import './featureFacets.styl';

const ImagesFacetsPane = View.extend({
    /**
     * @param {ImagesFacetCollection} settings.completeFacets
     * @param {ImagesFacetCollection} settings.filteredFacets
     * @param {ImagesFilter} settings.filters
     */
    initialize: function (settings) {
        this.completeFacets = settings.completeFacets;
        this.filteredFacets = settings.filteredFacets;
        this.filters = settings.filters;

        // TODO: Use the more general 'update' event, once Girder's version of Backbone is upgraded
        // TODO: ensure this fires when facets are modified in-place
        this.listenTo(this.completeFacets, 'sync', this.render);

        this._facetViews = [];
    },

    render: function () {
        _.each(this.facetViews, (facetView) => {
            facetView.destroy();
        });
        this._facetViews = [];
        this.$el.empty();

        this.$el.html(ImagesFacetsPaneTemplate({
            filterHexColors: [
                '00ABFF', // for hover on check buttons
                'CCCCCC' // for buttons with ".disabled" (possibly not used)
            ]
        }));

        this.completeFacets.forEach((completeFacet) => {
            const facetId = completeFacet.id;

            let headerEl = null;
            if (facetId === 'meta.clinical.diagnosis' || facetId === 'meta.clinical.benign_malignant') {
                headerEl = this.$('.isic-images-facets-diagnosis');
            } else if (facetId.startsWith('meta.clinical')) {
                headerEl = this.$('.isic-images-facets-clinical');
            } else if (facetId.startsWith('meta.acquisition')) {
                headerEl = this.$('.isic-images-facets-acquisition');
            } else {
                headerEl = this.$('.isic-images-facets-database');
            }

            this._createFacetView(facetId)
                .$el.appendTo(headerEl);
        });

        _.each(this._facetViews, (facetView) => {
            facetView.render();
        });

        new FeatureFacetsSubsection({
            name: 'Metaphoric',
            level: 0,
            subFeatures: MultiselectableFeatureCollection.fromMasterFeatures(),
            parentView: this
        })
            .render()
            .$el.appendTo(this.$('.isic-images-facets-features>.isic-images-facets-features-section'));

        return this;
    },

    _createFacetView: function (facetId) {
        const completeFacet = this.completeFacets.get(facetId);
        const FacetView = completeFacet.schema().FacetView;
        const facetView = new FacetView({
            completeFacet: completeFacet,
            filteredFacet: this.filteredFacets.get(facetId),
            filter: this.filters.facetFilter(facetId),
            parentView: this
        });
        this._facetViews.push(facetView);
        return facetView;
    }
});

const FeatureFacetsSubsection = View.extend({
    className: 'isic-images-facets-features-section',

    events: {
        'click .isic-images-facets-feature-toggle': function (event) {
            this.childListEl.toggle();
            this.childListEl.siblings('.isic-images-facets-feature-toggle')
                .toggleClass('icon-down-open')
                .toggleClass('icon-right-open');
            event.stopPropagation();
        }
    },

    initialize: function (settings) {
        this.name = settings.name;
        this.level = settings.level;
        this.subFeatures = settings.subFeatures;

        this.childViews = _.chain(this.subFeatures.models)
            .groupBy((feature) => {
                return feature.get('name')[this.level + 1]
            })
            .map((childSubFeatures, childSubsectionName) => {
                if (childSubFeatures.length <= 1) {
                    return new FeatureFacetView({
                        name: childSubsectionName,
                        level: this.level + 1,
                        parentView: this
                    });
                } else {
                    return new FeatureFacetsSubsection({
                        name: childSubsectionName,
                        level: this.level + 1,
                        subFeatures: new MultiselectableFeatureCollection(childSubFeatures),
                        parentView: this
                    });
                }
            })
            .each((childView) => {
            })
            .value();
    },

    render: function () {
        this.$el.html(FeatureFacetsSubsectionTemplate({
            name: this.name
        }));
        // Must find this before children start adding their own sub-children?
        this.childListEl = this.$('.isic-images-facets-features-children');
        _.each(this.childViews, (childView) => {
            childView
                .render()
                .$el.appendTo(this.childListEl);
        });

        return this;
    }
});

const FeatureFacetView = View.extend({
    className: 'isic-images-facets-features-section',

    initialize: function (settings) {
        this.name = settings.name;
        this.level = settings.level;
    },

    render: function () {
        this.$el.html(FeatureFacetTemplate({
            name: this.name
        }));
        // TODO: remove this placeholder and replace with margin.
        this.$('.icon-right-open').css('visibility', 'hidden');
        return this;
    }
});



export default ImagesFacetsPane;
