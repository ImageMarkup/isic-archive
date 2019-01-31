import $ from 'jquery';

import {restRequest} from '@girder/core/rest';

import Model from './Model';

const ImageModel = Model.extend({
    resourceName: 'image',

    /**
     * Apply metadata to an image.
     * @param [metadata] Image metadata object.
     * @param [save] Whether to save the metadata to the image if validation succeeds.
     */
    applyMetadata: function (metadata, save) {
        const params = {
            save: save
        };

        return restRequest({
            url: `${this.resourceName}/${this.id}/metadata?` + $.param(params),
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify(metadata),
            error: null
        });
    }
});

export default ImageModel;
