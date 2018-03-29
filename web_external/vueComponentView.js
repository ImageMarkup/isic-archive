import Vue from 'vue';

import View from './view';

import store from './vue/store';

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

        this.vue = new Vue({
            el: vueContainer,
            store,
            render: (createElement) => {
                return createElement(this.component, {
                    props: this.props
                });
            }
        });

        return this;
    },

    destroy: function () {
        if (this.vue) {
            this.vue.$destroy();
        }

        View.prototype.destroy.call(this);
    }
});

export default VueComponentView;
