/**
 * Study resource.
 */

import StudyModel from '../../models/StudyModel';

export default {
    get(id) {
        const study = new StudyModel({_id: id});
        return study.fetch();
    }
};
