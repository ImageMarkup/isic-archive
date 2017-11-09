import $ from 'jquery';
import _ from 'underscore';

import FeatureCollection from '../collections/FeatureCollection';
import {MultiselectableFeatureCollection} from '../collections/FeatureCollection';
import View from '../view';

import SelectFeaturesWidgetTemplate from './selectFeaturseWidget.pug';
import  './selectFeaturseWidget.styl';
import SelectFeatureWidgetTemplate from './selectFeatureWidget.pug';
import SelectFeatureWidgetPopoverTemplate from './selectFeatureWidgetPopover.pug';

const SelectFeatureWidget = View.extend({
    events: {
        'change input': function () {
            if (this.$('input').prop('checked')) {
                this.model.select();
            } else {
                this.model.deselect();
            }
        }
    },

    /**
     * @param {FeatureModel} settings.model
     */
    initialize: function (settings) {
        this.featureDictionary = settings.featureDictionary;
        this.listenTo(this.model, 'selected deselected', this._updateState);
    },

    render: function () {
        this.$el.html(SelectFeatureWidgetTemplate({
            feature: this.model
        }));
        this.$('[data-toggle="popover"]').popover({
            title: _.escape(this.model.name()),
            content: SelectFeatureWidgetPopoverTemplate({
                feature: this.model,
                featureDictionary: this.featureDictionary
            }),
            html: true,
        });
        this._updateState();
    },

    _updateState: function () {
        this.$('input').prop('checked', !!this.model.selected);
    }
});

const SelectFeaturesWidget = View.extend({
    className: 'isic-selectFeatures',

    events: {
        // TODO: Add buttons for selectAll and reset
    },

    initialize: function (settings) {
        this.collection = MultiselectableFeatureCollection.fromFeatureDictionary();
    },

    render: function () {
        this.$el.html(SelectFeaturesWidgetTemplate());

        this.subWidgets = this.collection.map((feature) => {
            const subWidget = new SelectFeatureWidget({
                model: feature,
                featureDictionary: this.collection,
                parentView: this
            });

            let targetDiv;
            if (feature.get('type') === 'select') {
                targetDiv = this.$('.isic-selectFeatures-global');
            } else if (feature.get('type') === 'superpixel') {
                if (feature.get('nomenclature') === 'descriptive') {
                    targetDiv = this.$('.isic-selectFeatures-local-descriptive');
                } else if (feature.get('nomenclature') === 'metaphoric') {
                    targetDiv = this.$('.isic-selectFeatures-local-metaphoric');
                }
            }
            // TODO: fallthrough logic for default cases

            targetDiv.append(subWidget.$el);

            subWidget.render();
            return subWidget;
        });

        return this;
    },

    getSelectedFeatureIds: function () {
        // This will maintain the collection's ordering
        return _.pluck(this.collection.filter((model) => model.selected), 'id');
    }
});

export default SelectFeaturesWidget;
