import _ from 'underscore';

import {getCurrentUser} from 'girder/auth';
import {restRequest} from 'girder/rest';

import Model from './Model';
import FeaturesetModel from './FeaturesetModel';
import UserCollection from '../collections/UserCollection';
import UserModel from './UserModel';

var StudyModel = Model.extend({
    resourceName: 'study',

    creator: function () {
        return new UserModel(this.get('creator'));
    },

    /**
     * Return the featureset for this study.
     *
     * This returns a FeaturesetModel with only a few summary properties of
     * the featureset. To retrieve all properties of the featureset, call
     * ".fetch()" on the FeaturesetModel.
     */
    featureset: function () {
        return new FeaturesetModel(this.get('featureset'));
    },

    users: function () {
        var userModels = this.get('users').map((user) => {
            return new UserModel(user);
        });
        return new UserCollection(userModels);
    },

    /**
     * Add a user to the study.
     */
    addUser: function (userId) {
        // TODO: return a promise here, and use it (rather than events)
        restRequest({
            path: `${this.resourceName}/${this.id}/users`,
            type: 'POST',
            data: {
                userIds: JSON.stringify([userId])
            }
        }).done((resp) => {
            this.trigger('g:addedUser');
        }).fail((err) => {
            this.trigger('g:error', err);
        });
    },

    removeUser: function (user) {
        return restRequest({
            path: `${this.resourceName}/${this.id}/users/${user.id}`,
            type: 'DELETE',
            error: null
        });
        // TODO: update the model in-place here, with the new list of annotators,
        // then trigger a changed event
    },

    destroy: function (options) {
        // Don't modify the "options", but override some properties
        var params = _.clone(options);
        // Study deletion may fail if it has completed annotations
        params.wait = true;

        return Model.prototype.destroy.call(this, params);
    },

    canAdmin: function () {
        var user = getCurrentUser();
        return user && user.canAdminStudy();
    }
});

export default StudyModel;
