/**
 * Segmentations resource.
 */

import { restRequest } from '@girder/core/rest';

export default {
    getSegmentationsForImage(id) {
        return restRequest({
            url: `segmentation`,
            data: {
                imageId: id,
                limit: 0
            },
            method: 'GET',
            error: null
        });
    },
    submitReview(id, approved) {
        return restRequest({
            url: `segmentation/${id}/review`,
            data: {
                approved: approved
            },
            method: 'POST',
            error: null
        });
    }
};
