/**
 * Main Vuex store.
 */

import Vue from 'vue';
import Vuex from 'vuex';

import annotate from '../components/AnnotationTool/AnnotationToolStore';
import datasetReview from '../components/DatasetReview/DatasetReviewStore';
import segmentationReview from '../components/SegmentationReview/SegmentationReviewStore';

Vue.use(Vuex);

export default new Vuex.Store({
    modules: {
        annotate,
        datasetReview,
        segmentationReview
    }
});
