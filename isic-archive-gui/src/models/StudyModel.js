import _ from 'underscore';

import {getCurrentUser} from '@girder/core/auth';
import {restRequest} from '@girder/core/rest';

import Model from './Model';
import UserCollection from '../collections/UserCollection';
import UserModel from './UserModel';

const StudyModel = Model.extend({
    resourceName: 'study',

    creator: function () {
        return new UserModel(this.get('creator'));
    },

    users: function () {
        let userModels = this.get('users').map((user) => {
            return new UserModel(user);
        });
        return new UserCollection(userModels);
    },

    /**
     * Users requesting to participate in the study.
     */
    participationRequests: function () {
        let userModels = this.get('participationRequests').map((user) => {
            return new UserModel(user);
        });
        return new UserCollection(userModels);
    },

    /**
     * Add a user to the study.
     */
    addUser: function (user) {
        return restRequest({
            url: `${this.resourceName}/${this.id}/users`,
            method: 'POST',
            data: {
                userIds: JSON.stringify([user.id])
            }
        });
    },

    removeUser: function (user) {
        return restRequest({
            url: `${this.resourceName}/${this.id}/users/${user.id}`,
            method: 'DELETE',
            error: null
        });
        // TODO: update the model in-place here, with the new list of annotators,
        // then trigger a changed event
    },

    deleteParticipationRequest: function (user) {
        return restRequest({
            url: `${this.resourceName}/${this.id}/participate/${user.id}`,
            method: 'DELETE',
            error: null
        });
    },

    destroy: function (options) {
        // Don't modify the "options", but override some properties
        let params = _.clone(options);
        // Study deletion may fail if it has completed annotations
        params.wait = true;

        return Model.prototype.destroy.call(this, params);
    },

    canAdmin: function () {
        let user = getCurrentUser();
        return user && user.canAdminStudy();
    }
});

export default StudyModel;
