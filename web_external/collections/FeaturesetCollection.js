import {getCurrentUser} from 'girder/auth';

import Collection from './Collection';
import FeaturesetModel from '../models/FeaturesetModel';

const FeaturesetCollection = Collection.extend({
    resourceName: 'featureset',
    model: FeaturesetModel
}, {
    canCreate: function () {
        var user = getCurrentUser();
        return user && user.canAdminStudy();
    }
});

export default FeaturesetCollection;
