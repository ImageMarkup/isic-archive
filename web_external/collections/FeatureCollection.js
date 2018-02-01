import _ from 'underscore'
import Backbone from 'backbone';
import 'backbone.select';

import {restRequest} from 'girder/rest';

import {SelectFeatureModel, SuperpixelFeatureModel} from '../models/FeatureModel';
import masterFeatures from '../masterFeatures.json';

_.forEach(masterFeatures, (feature) => {
    if (feature.type === 'superpixel') {
        feature.id = [feature.nomenclature].concat(feature.name).join(':');
    }
});

// masterFeatures.sort((a, b) => {
//     // Sort first type 'type', then by 'name'
//     // TODO: This would probably be easier with Lodash's "sortBy"
//     if (a.type < b.type) {
//         return -1;
//     } else if (a.type > b.type) {
//         return 1;
//     } else {
//         return a.name < b.name ? -1 : 1;
//     }
// });

const FeatureCollection = Backbone.Collection.extend({
    model: function (attrs, options) {
        if (attrs.type === 'select') {
            return new SelectFeatureModel(attrs, options);
        } else if (attrs.type === 'superpixel') {
            return new SuperpixelFeatureModel(attrs, options);
        } else {
            throw new Error(`Unknown Feature type: ${attrs.type}`);
        }
    },

    modelId: _.property('id'),

    filterType: function (type) {
        // This is an array. Wrapping it in a new collection should be fine, since the "collection"
        // property of each model should stay set to the original collection, but until we need
        // collection-specific functionality, it's safer and simpler to not do so.
        return this.filter((model) => model.get('type') === type);
    }

}, {
    fromMasterFeatures: function () {
        return new FeatureCollection(masterFeatures);
    }
});

const SelectableFeatureCollection = FeatureCollection.extend({
    initialize: function (models) {
        Backbone.Select.One.applyTo(this, models);
        FeatureCollection.prototype.initialize.apply(this, arguments);
    }
}, {
    fromMasterFeatures: function () {
        return new SelectableFeatureCollection(masterFeatures);
    }
});

const MultiselectableFeatureCollection = FeatureCollection.extend({
    initialize: function (models) {
        Backbone.Select.Many.applyTo(this, models);
        FeatureCollection.prototype.initialize.apply(this, arguments);
    }
}, {
    fromMasterFeatures: function () {
        return new MultiselectableFeatureCollection(masterFeatures);
    }
});

export default FeatureCollection;
export {SelectableFeatureCollection, MultiselectableFeatureCollection};
