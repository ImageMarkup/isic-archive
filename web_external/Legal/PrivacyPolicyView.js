import View from '../view';

import PrivacyPolicyPageTemplate from './privacyPolicyPage.pug';
import './legal.styl';

const PrivacyPolicyView = View.extend({
    initialize: function (settings) {
        this.render();
    },

    render: function () {
        this.$el.html(PrivacyPolicyPageTemplate());

        return this;
    }
});

export default PrivacyPolicyView;
