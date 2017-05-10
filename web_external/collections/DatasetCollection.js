import {getCurrentUser} from 'girder/auth';

import Collection from './Collection';
import DatasetModel from '../models/DatasetModel';

var DatasetCollection = Collection.extend({
    resourceName: 'dataset',
    model: DatasetModel
}, {
    canCreate: function () {
        var user = getCurrentUser();
        return user && user.canCreateDataset();
    }
});

export default DatasetCollection;
