import {getCurrentUser} from 'girder/auth';

import View from '../view';

import LayoutHeaderTemplate from './layoutHeader.pug';
import './layoutHeader.styl';

const LayoutHeaderView = View.extend({
    initialize: function (settings) {
        this.render();
    },

    render: function () {
        this.$el.html(LayoutHeaderTemplate({
            currentUser: getCurrentUser()
        }));

        return this;
    }
});

export default LayoutHeaderView;
