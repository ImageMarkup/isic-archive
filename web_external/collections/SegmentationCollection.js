import Backbone from 'backbone';
import 'backbone.select';

import {SORT_DESC} from 'girder/constants';

import Collection from './Collection';
import SegmentationModel from '../models/SegmentationModel';

const SegmentationCollection = Collection.extend({
    resourceName: 'segmentation',
    model: SegmentationModel,
    sortField: 'created',
    sortDir: SORT_DESC
});

const SelectableSegmentationCollection = SegmentationCollection.extend({
    initialize: function (models) {
        Backbone.Select.One.applyTo(this, models);
        SegmentationCollection.prototype.initialize.apply(this, arguments);
    }
});

export default SegmentationCollection;
export {SelectableSegmentationCollection};
