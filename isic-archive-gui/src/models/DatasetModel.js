import $ from 'jquery';

import {getCurrentUser} from '@girder/core/auth';
import {AccessType} from '@girder/core/constants';
import {restRequest, getApiRoot} from '@girder/core/rest';

import {AccessControlledModel} from './Model';
import UserModel from './UserModel';

const DatasetModel = AccessControlledModel.extend({
    resourceName: 'dataset',

    creator: function () {
        return new UserModel(this.get('creator'));
    },

    /**
     * Upload a batch of images.
     * @param [zipFileId] The ID of the .zip file.
     * @param [signature] Signature of license agreement.
     */
    uploadBatch: function (zipFileId, signature) {
        return restRequest({
            url: `${this.resourceName}/${this.id}/zipBatch`,
            method: 'POST',
            data: {
                zipFileId: zipFileId,
                signature: signature
            },
            error: null
        });
    },

    /**
     * Upload an image.
     * @param [filename] Image filename.
     * @param [signature] Signature of license agreement.
     * @param [imageData] Image data.
     */
    uploadImage: function (filename, signature, imageData) {
        const params = {
            filename: filename,
            signature: signature
        };

        return restRequest({
            url: `${this.resourceName}/${this.id}/image?` + $.param(params),
            method: 'POST',
            data: imageData,
            contentType: false,
            processData: false,
            error: null
        });
    },

    /**
     * Register metadata with the dataset.
     * @param [filename] Metadata filename.
     * @param [metadataData] Metadata data.
     */
    registerMetadata: function (filename, metadataData) {
        const params = {
            filename: filename
        };

        return restRequest({
            url: `${this.resourceName}/${this.id}/metadata?` + $.param(params),
            method: 'POST',
            data: metadataData,
            contentType: false,
            processData: false,
            error: null
        });
    },

    /**
     * Get the registered metadata for the dataset. Returns a promise.
     */
    getRegisteredMetadata: function () {
        let deferred = $.Deferred();
        restRequest({
            url: `${this.resourceName}/${this.id}/metadata`
        }).done((resp) => {
            deferred.resolve(resp);
        });
        return deferred.promise();
    },

    /**
     * Apply registered metadata to the dataset. Returns a promise.
     * @param [metadataFileId] The ID of the metadata file.
     */
    applyMetadata: function (metadataFileId, save) {
        let deferred = $.Deferred();
        restRequest({
            url: `${this.resourceName}/${this.id}/metadata/${metadataFileId}/apply`,
            method: 'POST',
            data: {
                save: save
            },
            error: null
        }).done((resp) => {
            deferred.resolve(resp);
        }).fail((err) => {
            deferred.reject(err);
        });
        return deferred.promise();
    },

    /**
     * Download a registered metadata file.
     * @param [metadataFileId] The ID of the metadata file.
     */
    downloadMetadata: function (metadataFileId) {
        const downloadUrl = `${getApiRoot()}/${this.resourceName}/${this.id}/metadata/${metadataFileId}/download`;
        window.location.assign(downloadUrl);
    },

    canWrite: function () {
        return this.get('_accessLevel') >= AccessType.WRITE;
    },

    canAdmin: function () {
        return this.get('_accessLevel') >= AccessType.ADMIN;
    }
}, {
    canCreate: function () {
        let user = getCurrentUser();
        return user && user.canCreateDataset();
    }
});

export default DatasetModel;
