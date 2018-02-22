import Vue from 'vue';

import View from './view';

// Backbone view that wraps a Vue component
const VueComponentView = View.extend({
    initialize: function (settings) {
        this.component = settings.component;
        this.props = settings.props;
        this.render();
    },

    render: function () {
        const vueContainer = $('<div></div>').get(0);
        this.$el.append(vueContainer);

        new Vue({ // eslint-disable-line no-new
            el: vueContainer,
            render: (createElement) => {
                return createElement(this.component, {
                    props: this.props
                });
            }
        });

        return this;
    }
});

export default VueComponentView;
