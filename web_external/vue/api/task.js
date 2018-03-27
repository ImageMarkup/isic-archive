/**
 * Task resource.
 */

import { restRequest } from 'girder/rest';

export default {
    getNextAnnotation(id) {
        return restRequest({
            url: `task/me/annotation/next`,
            data: {
                studyId: id
            },
            method: 'GET',
            error: null
        });
    }
};
