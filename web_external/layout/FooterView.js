import $ from 'jquery';

import {getApiRoot} from 'girder/rest';

import View from '../view';

import LayoutFooterTemplate from './layoutFooter.pug';
import './layoutFooter.styl';

const LayoutFooterView = View.extend({
    initialize: function (settings) {
        this.render();
    },

    render: function () {
        this.$el.html(LayoutFooterTemplate({
            apiRoot: getApiRoot()
        }));

        this.$('.isic-footer-disclaimer')
            .popover({
                trigger: 'hover',
                placement: 'auto top',
                container: this.$('.isic-footer-legal')
            })
            .click(function () {
                $(this).popover('toggle');
            });

        return this;
    }
});

export default LayoutFooterView;
