import {getCurrentUser} from 'girder/auth';

import Collection from './Collection';
import StudyModel from '../models/StudyModel';

const StudyCollection = Collection.extend({
    resourceName: 'study',
    model: StudyModel
}, {
    canCreate: function () {
        var user = getCurrentUser();
        return user && user.canAdminStudy();
    }
});

export default StudyCollection;
