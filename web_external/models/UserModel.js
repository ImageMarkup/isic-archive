import _ from 'underscore';
import $ from 'jquery';

import {getCurrentUser} from 'girder/auth';
import UserModel from 'girder/models/UserModel';
import {restRequest} from 'girder/rest';

// Fallback variable for anonymous user with no local storage
let acceptTerms = null;

// Add additional instance methods
UserModel.prototype.name = function () {
    let realName;
    if (this.has('login')) {
        realName = `${this.get('firstName')} ${this.get('lastName')} (${this.get('login')})`;
    }

    let displayName;
    if (this.has('name')) {
        displayName = this.get('name');
        if (realName) {
            displayName += ` [${realName}]`;
        }
    } else {
        // The user should always have either a 'login' or a 'name'
        displayName = realName;
    }
    return displayName;
};

UserModel.prototype.canAcceptTerms = function () {
    return this.get('permissions').acceptTerms === true;
};

UserModel.prototype.setAcceptTerms = function () {
    return restRequest({
        url: 'user/acceptTerms',
        method: 'POST'
    })
        .then((resp) => {
            if (_.has(resp, 'extra') && resp.extra === 'hasPermission') {
                // Directly update user permissions
                this.get('permissions').acceptTerms = true;
                this.trigger('change:permissions');
                return resp;
            } else {
                // This should not fail
                throw resp;
            }
        });
};

UserModel.prototype.canCreateDataset = function () {
    return this.get('permissions').createDataset;
};

UserModel.prototype.setCanCreateDataset = function () {
    return restRequest({
        url: 'user/requestCreateDatasetPermission',
        method: 'POST'
    })
        .then((resp) => {
            if (_.has(resp, 'extra') && resp.extra === 'hasPermission') {
                // Directly update user permissions
                this.get('permissions').createDataset = true;
                this.trigger('change:permissions');
                return resp;
            } else {
                throw resp;
            }
        });
};

UserModel.prototype.canReviewDataset = function () {
    return this.get('permissions').reviewDataset;
};

UserModel.prototype.getSegmentationSkill = function () {
    return this.get('permissions').segmentationSkill;
};

UserModel.prototype.canAdminStudy = function () {
    return this.get('permissions').adminStudy;
};

// Add additional static methods
UserModel.currentUserCanAcceptTerms = function () {
    let currentUser = getCurrentUser();
    if (currentUser) {
        return currentUser.canAcceptTerms();
    } else {
        return (window.localStorage.getItem('acceptTerms') === 'true') ||
               (acceptTerms === true);
    }
};

UserModel.currentUserSetAcceptTerms = function () {
    const currentUser = getCurrentUser();
    if (currentUser) {
        return currentUser.setAcceptTerms();
    } else {
        try {
            window.localStorage.setItem('acceptTerms', 'true');
        } catch (e) {
            acceptTerms = true;
        }
        return $.Deferred().resolve().promise();
    }
};

// Re-export, so all of ISIC can import it from here, and ensure the patched version gets used
export default UserModel;
