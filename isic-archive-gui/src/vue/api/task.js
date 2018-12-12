/**
 * Task resource.
 */

import { restRequest } from 'girder/rest';

export default {
    getNextImageForSegmentation(id) {
        return restRequest({
            url: `task/me/segmentation/next`,
            data: {
                datasetId: id
            },
            method: 'GET',
            error: null
        });
    },
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
