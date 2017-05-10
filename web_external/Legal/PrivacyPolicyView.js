import View from '../view';

import PrivacyPolicyPageTemplate from './privacyPolicyPage.jade';
import './legal.styl';

var PrivacyPolicyView = View.extend({
    initialize: function (settings) {
        this.render();
    },

    render: function () {
        this.$el.html(PrivacyPolicyPageTemplate());

        return this;
    }
});

export default PrivacyPolicyView;
