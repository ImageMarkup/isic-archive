/**
 * Image resource.
 */

import ImageModel from '../../models/ImageModel';

export default {
    get(id) {
        const image = new ImageModel({_id: id});
        return image.fetch();
    }
};
