import Backbone from 'backbone';

import UserModel from '../models/UserModel';
import TermsOfUseWidget from '../common/TermsOfUse/TermsOfUseWidget';
import View from '../view';
import router from '../router';

import TermsAcceptancePageTemplate from './termsAcceptancePage.pug';
import './termsAcceptancePage.styl';

const TermsAcceptanceView = View.extend({
    events: {
        'click #isic-terms-accept': function (event) {
            // Disable buttons while request is pending
            this.$('.isic-terms-agreement-button-container button').girderEnable(false);

            UserModel.currentUserSetAcceptTerms()
                .always(() => {
                    // Refresh page
                    Backbone.history.loadUrl();
                });
        },
        'click #isic-terms-reject': function (event) {
            // Route to home page
            router.navigate('', {trigger: true});
        }
    },

    initialize: function (settings) {
        this.termsOfUseWidget = new TermsOfUseWidget({
            parentView: this
        });

        this.render();
    },

    render: function () {
        this.$el.html(TermsAcceptancePageTemplate());

        this.termsOfUseWidget.setElement(
            this.$('#isic-terms-of-use-container')).render();

        return this;
    }
});

export default TermsAcceptanceView;
