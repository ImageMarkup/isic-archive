import Collection from './Collection';
import DatasetModel from '../models/DatasetModel';

const DatasetCollection = Collection.extend({
    resourceName: 'dataset',
    model: DatasetModel,
    sortField: '_id'
});

export default DatasetCollection;
