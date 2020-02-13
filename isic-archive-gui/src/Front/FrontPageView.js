import View from '../view';

import FrontPageTemplate from './frontPage.pug';
import './frontPage.styl';

const FrontPageView = View.extend({
    initialize: function (settings) {
        this.render();
        this.$el.addClass('isic-body-nopad');
    },

    render: function () {
        this.$el.html(FrontPageTemplate({
            isicApiRoot: process.env.VUE_APP_ISIC_API_ROOT,
        }));

        return this;
    }
});

export default FrontPageView;
