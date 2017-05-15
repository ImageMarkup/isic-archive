import View from '../view';

import TermsOfUsePageTemplate from './termsOfUsePage.pug';
import './legal.styl';

const TermsOfUseView = View.extend({
    initialize: function (settings) {
        this.render();
    },

    render: function () {
        this.$el.html(TermsOfUsePageTemplate());

        return this;
    }
});

export default TermsOfUseView;
