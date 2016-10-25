isic.View = girder.View.extend({

    // Format a user model or user object as a string
    formatUser: function (user) {
        if (user instanceof girder.models.UserModel) {
            user = user.attributes;
        }

        var str = null;
        if (_.has(user, 'firstName') && _.has(user, 'lastName')) {
            str = user['firstName'] + ' ' + user['lastName'] + ' (' + user['login'] + ')';
        } else {
            str = user['login'];
        }
        return str;
    },

    // Format a featureset model or featureset object as a string
    formatFeatureset: function (featureset) {
        if (featureset instanceof isic.models.FeaturesetModel) {
            featureset = featureset.attributes;
        }
        return featureset['name'] + ' (version ' + featureset['version'] + ')';
    }
});
