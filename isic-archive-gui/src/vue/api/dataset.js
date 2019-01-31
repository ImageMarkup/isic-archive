/**
 * Dataset resource.
 */

import { restRequest } from '@girder/core/rest';

import DatasetModel from '../../models/DatasetModel';

export default {
    get(id) {
        const dataset = new DatasetModel({_id: id});
        return dataset.fetch();
    },
    getReviewImages(id) {
        return restRequest({
            url: `dataset/${id}/review`,
            method: 'GET',
            data: {
                limit: 50
            }
        });
    },
    submitReview(id, data) {
        return restRequest({
            url: `dataset/${id}/review`,
            method: 'POST',
            data: JSON.stringify(data),
            contentType: 'application/json'
        });
    }
};
