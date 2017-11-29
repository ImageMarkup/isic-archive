import Backbone from 'backbone';
import 'backbone.select';

import {getCurrentUser} from 'girder/auth';

import Collection from './Collection';
import DatasetModel from '../models/DatasetModel';

const DatasetCollection = Collection.extend({
    resourceName: 'dataset',
    model: DatasetModel,
    sortField: '_id'
}, {
    canCreate: function () {
        let user = getCurrentUser();
        return user && user.canCreateDataset();
    }
});

const SelectableDatasetCollection = DatasetCollection.extend({
    initialize: function (models) {
        Backbone.Select.One.applyTo(this, models);
        DatasetCollection.prototype.initialize.apply(this, arguments);
    }
});

export default DatasetCollection;
export {SelectableDatasetCollection};
