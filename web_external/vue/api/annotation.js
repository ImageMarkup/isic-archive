/**
 * Annotation resource.
 */

import { restRequest } from 'girder/rest';

import AnnotationModel from '../../models/AnnotationModel';

export default {
    get(id) {
        const annotation = new AnnotationModel({_id: id});
        return annotation.fetch();
    },
    submit(id, annotation) {
        return restRequest({
            url: `annotation/${id}`,
            method: 'PUT',
            data: JSON.stringify(annotation),
            contentType: 'application/json'
        });
    }
};
