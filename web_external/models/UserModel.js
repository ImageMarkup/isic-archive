isic.models.UserModel = girder.models.UserModel.extend({
    name: function () {
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
    },

    canAcceptTerms: function () {
        return this.get('permissions').acceptTerms === true;
    },
    setAcceptTerms: function (successCallback) {
        girder.restRequest({
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
    },
    canCreateDataset: function () {
        return this.get('permissions').createDataset;
    },
    setCanCreateDataset: function (successCallback, failureCallback) {
        girder.restRequest({
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
    },
    canReviewDataset: function () {
        return this.get('permissions').reviewDataset;
    },
    getSegmentationSkill: function () {
        return this.get('permissions').segmentationSkill;
    },
    canAdminStudy: function () {
        return this.get('permissions').adminStudy;
    }
}, {
    // Static methods
    currentUserCanAcceptTerms: function () {
        if (girder.currentUser) {
            return girder.currentUser.canAcceptTerms();
        } else {
            return (window.localStorage.getItem('acceptTerms') === 'true') ||
                   (isic.acceptTerms === true);
        }
    },
    currentUserSetAcceptTerms: function (successCallback) {
        if (girder.currentUser) {
            girder.currentUser.setAcceptTerms(successCallback);
        } else {
            try {
                window.localStorage.setItem('acceptTerms', 'true');
            } catch (e) {
                isic.acceptTerms = true;
            }
            successCallback();
        }
    }
}

);
