import View from '../view';

import MedicalDisclaimerPageTemplate from './medicalDisclaimerPage.jade';
import './legal.styl';

var MedicalDisclaimerView = View.extend({
    initialize: function (settings) {
        this.render();
    },

    render: function () {
        this.$el.html(MedicalDisclaimerPageTemplate());

        return this;
    }
});

export default MedicalDisclaimerView;
