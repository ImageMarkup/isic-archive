/**
 * Main Vuex store.
 */

import Vue from 'vue';
import Vuex from 'vuex';

import annotate from '../components/AnnotationTool/AnnotationToolStore';

Vue.use(Vuex);

export default new Vuex.Store({
    modules: {
        annotate
    }
});
