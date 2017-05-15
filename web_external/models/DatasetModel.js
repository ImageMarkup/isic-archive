import $ from 'jquery';

import {getCurrentUser} from 'girder/auth';
import {restRequest} from 'girder/rest';

import Model from './Model';
import UserModel from './UserModel';

const DatasetModel = Model.extend({
    resourceName: 'dataset',

    creator: function () {
        return new UserModel(this.get('creator'));
    },

     /**
     * Create a new dataset from a .zip file of images.
     * @param [zipFileId] The ID of the .zip file.
     * @param [name] Name of the dataset.
     * @param [owner] Owner of the dataset.
     * @param [description] Description of the dataset.
     * @param [license] License of the dataset.
     * @param [signature] Signature of license agreement.
     * @param [anonymous] Whether to use an anonymous attribution for the dataset.
     * @param [attribution] Attribution of the dataset.
     */
    ingestImages: function (zipFileId, name, owner, description, license,
        signature, anonymous, attribution) {
        restRequest({
            path: this.resourceName,
            type: 'POST',
            data: {
                zipFileId: zipFileId,
                name: name,
                owner: owner,
                description: description,
                license: license,
                signature: signature,
                anonymous: anonymous,
                attribution: attribution
            },
            error: null
        }).done((resp) => {
            this.set(resp);
            this.trigger('isic:ingestImages:success', resp);
        }).fail((err) => {
            this.trigger('isic:ingestImages:error', err);
        });
    },

     /**
     * Register a metadata file with the dataset.
     * @param [metadataFileId] The ID of the metadata file.
     */
    registerMetadata: function (metadataFileId) {
        restRequest({
            path: `${this.resourceName}/${this.id}/metadata`,
            type: 'POST',
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
        var deferred = $.Deferred();
        restRequest({
            path: `${this.resourceName}/${this.id}/metadata`
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
        var deferred = $.Deferred();
        restRequest({
            path: `${this.resourceName}/${this.id}/metadata/${metadataFileId}`,
            type: 'POST',
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

    canAdmin: function () {
        var user = getCurrentUser();
        return user && user.canAdminStudy();
    }
});

export default DatasetModel;
