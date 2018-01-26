import $ from 'jquery';

import {getCurrentUser} from 'girder/auth';
import {AccessType} from 'girder/constants';
import {restRequest} from 'girder/rest';

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
            url: `${this.resourceName}/${this.id}/zip`,
            method: 'POST',
            data: {
                zipFileId: zipFileId,
                signature: signature
            },
            error: null
        });
    },

    /**
     * Register a metadata file with the dataset.
     * @param [metadataFileId] The ID of the metadata file.
     */
    registerMetadata: function (metadataFileId) {
        restRequest({
            url: `${this.resourceName}/${this.id}/metadata`,
            method: 'POST',
            data: {
                metadataFileId: metadataFileId
            },
            error: null
        }).done((resp) => {
            this.trigger('isic:registerMetadata:success', resp);
        }).fail((err) => {
            this.trigger('isic:registerMetadata:error', err);
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
            url: `${this.resourceName}/${this.id}/metadata/${metadataFileId}`,
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
