import {getCurrentUser} from '@girder/core/auth';

import Collection from './Collection';
import StudyModel from '../models/StudyModel';

const StudyCollection = Collection.extend({
    resourceName: 'study',
    model: StudyModel
}, {
    canCreate: function () {
        let user = getCurrentUser();
        return user && user.canAdminStudy();
    }
});

export default StudyCollection;
