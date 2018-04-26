/**
 * Dataset Review Vuex store.
 */

import _ from 'underscore';
import Vue from 'vue';

import { getApiRoot } from 'girder/rest';

import DatasetService from '../../api/dataset';

export const SubmissionState = {
    UNSUBMITTED: 'unsubmitted',
    SUBMITTING: 'submitting',
    SUBMITTED: 'submitted',
    FAILED: 'failed'
};

export default {
    namespaced: true,
    state: {
        dataset: null,
        images: [],
        submissionState: SubmissionState.UNSUBMITTED,
        thumbnailWidth: 768
    },
    getters: {
        acceptedImages(state) {
            return state.images.filter((image) => {
                return !image.flagged;
            });
        },
        flaggedImages(state) {
            return state.images.filter((image) => {
                return image.flagged;
            });
        }
    },
    mutations: {
        setDataset(state, dataset) {
            state.dataset = dataset;
        },
        setImages(state, images) {
            state.images = images;
        },
        toggleFlagged(state, index) {
            Vue.set(state.images[index], 'flagged', !state.images[index].flagged);
        },
        setSubmissionState(state, data) {
            state.submissionState = data;
        }
    },
    actions: {
        loadDataset({ dispatch, commit }, { id }) {
            // Reset state
            commit('setDataset', null);
            commit('setImages', []);
            commit('setSubmissionState', SubmissionState.UNSUBMITTED);

            // Fetch dataset
            DatasetService.get(id)
                .done((resp) => {
                    commit('setDataset', resp);
                });

            // Fetch review images
            dispatch('loadReviewImages', {id: id});
        },
        loadReviewImages({ state, commit }, { id }) {
            DatasetService.getReviewImages(id)
                .done((resp) => {
                    const images = resp.map((image) => {
                        image.thumbnail = `${getApiRoot()}/item/${image._id}/tiles/region?width=${state.thumbnailWidth}`;

                        image.diagnosisStrings = [];
                        [
                            'benign_malignant',
                            'diagnosis',
                            'diagnosis_confirm_type'
                        ].forEach((key) => {
                            const value = image.meta.clinical[key] || image.meta.unstructured[key];
                            if (value) {
                                image.diagnosisStrings.push(`${key}: ${value}`);
                            }
                        });

                        image.flagged = false;

                        return image;
                    });

                    commit('setImages', images);
                });
        },
        submitReview({ state, getters, commit }) {
            commit('setSubmissionState', SubmissionState.SUBMITTING);

            const acceptedImageIds = _.pluck(getters.acceptedImages, '_id');
            const flaggedImageIds = _.pluck(getters.flaggedImages, '_id');

            const data = {
                accepted: acceptedImageIds,
                flagged: flaggedImageIds
            };

            DatasetService.submitReview(state.dataset._id, data)
                .done(() => commit('setSubmissionState', SubmissionState.SUBMITTED))
                .fail(() => commit('setSubmissionState', SubmissionState.FAILED));
        }
    }
};
