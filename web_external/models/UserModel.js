import _ from 'underscore';

import events from 'girder/events';
import eventStream from 'girder/utilities/EventStream';
import {getCurrentUser, setCurrentUser} from 'girder/auth';
import UserModel from 'girder/models/UserModel';
import {restRequest} from 'girder/rest';

// Fallback variable for anonymous user with no local storage
var acceptTerms = null;

// Add additional instance methods
UserModel.prototype.name = function () {
    var realName;
    if (this.has('login')) {
        realName =
            this.get('firstName') +
            ' ' + this.get('lastName') +
            ' (' + this.get('login') + ')';
    }

    var displayName;
    if (this.has('name')) {
        displayName = this.get('name');
        if (realName) {
            displayName += ' [' + realName + ']';
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

UserModel.prototype.setAcceptTerms = function (successCallback) {
    restRequest({
        path: 'user/acceptTerms',
        type: 'POST'
    }).done(_.bind(function (resp) {
        if (_.has(resp, 'extra') && resp.extra === 'hasPermission') {
            // Directly update user permissions
            this.get('permissions').acceptTerms = true;
            this.trigger('change:permissions');
            successCallback(resp);
        }
        // This should not fail
    }, this));
};

UserModel.prototype.canCreateDataset = function () {
    return this.get('permissions').createDataset;
};

UserModel.prototype.setCanCreateDataset = function (successCallback, failureCallback) {
    restRequest({
        path: 'user/requestCreateDatasetPermission',
        type: 'POST'
    }).done(_.bind(function (resp) {
        if (_.has(resp, 'extra') && resp.extra === 'hasPermission') {
            // Directly update user permissions
            this.get('permissions').createDataset = true;
            this.trigger('change:permissions');
            successCallback(resp);
        } else {
            failureCallback(resp);
        }
    }, this));
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

// Patch upstream changePassword to return a promise
// TODO: Remove this once Girder is updated
UserModel.prototype.changePassword = function (oldPassword, newPassword) {
    return restRequest({
        path: this.resourceName + '/password',
        data: {
            old: oldPassword,
            new: newPassword
        },
        type: 'PUT',
        error: null
    })
    .done(_.bind(function () {
        this.trigger('g:passwordChanged');
    }, this))
    .fail(_.bind(function (err) {
        this.trigger('g:error', err);
    }, this));
};

// Add additional static methods
// TODO: Push temporaryTokenLogin to upstream Girder
UserModel.temporaryTokenLogin = function (userId, token) {
    return restRequest({
        path: 'user/password/temporary/' + userId,
        type: 'GET',
        data: {token: token},
        error: null
    })
    .done(_.bind(function (resp) {
        resp.user.token = resp.authToken.token;
        eventStream.close();
        setCurrentUser(new UserModel(resp.user));
        eventStream.open();
        events.trigger('g:login-changed');
    }, this));
};

UserModel.currentUserCanAcceptTerms = function () {
    var currentUser = getCurrentUser();
    if (currentUser) {
        return currentUser.canAcceptTerms();
    } else {
        return (window.localStorage.getItem('acceptTerms') === 'true') ||
               (acceptTerms === true);
    }
};

UserModel.currentUserSetAcceptTerms = function (successCallback) {
    var currentUser = getCurrentUser();
    if (currentUser) {
        currentUser.setAcceptTerms(successCallback);
    } else {
        try {
            window.localStorage.setItem('acceptTerms', 'true');
        } catch (e) {
            acceptTerms = true;
        }
        successCallback();
    }
};

// Re-export, so all of ISIC can import it from here, and ensure the patched version gets used
export default UserModel;
