import router from '../router';
import View from '../view';

import FrontPageTemplate from './frontPage.pug';
import './frontPage.styl';

const FrontPageView = View.extend({
    events: {
        'click .isic-frontpage-about': function () {
            router.navigate('about', {trigger: true});
        },
        'click .isic-frontpage-images': function () {
            router.navigate('images', {trigger: true});
        },
        'click .isic-frontpage-challenges': function () {
            router.navigate('challenges', {trigger: true});
        },
        'click .isic-frontpage-upload': function () {
            router.navigate('dataset/create', {trigger: true});
        },
        'click .isic-frontpage-studies': function () {
            router.navigate('studies', {trigger: true});
        },
        'click .isic-frontpage-dermoscopedia': function () {
            router.navigate('dermoscopedia', {trigger: true});
        },
        'click .isic-frontpage-dashboard': function () {
            router.navigate('tasks', {trigger: true});
        },
        'click .isic-frontpage-api': function () {
            router.navigate('api', {trigger: true});
        }
    },

    initialize: function (settings) {
        this.render();
        this.$el.addClass('isic-body-nopad');
    },

    render: function () {
        this.$el.html(FrontPageTemplate());

        return this;
    }
});

export default FrontPageView;
