import View from '../view';

import TermsOfUsePageTemplate from './termsOfUsePage.pug';
import './legal.styl';

var TermsOfUseView = View.extend({
    initialize: function (settings) {
        this.render();
    },

    render: function () {
        this.$el.html(TermsOfUsePageTemplate());

        return this;
    }
});

export default TermsOfUseView;
