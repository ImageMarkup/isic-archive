/**
 * Annotation tool Vuex store.
 */

import _ from 'underscore';
import Vue from 'vue';

import AnnotationService from '../../api/annotation';
import ImageService from '../../api/image';
import StudyService from '../../api/study';
import TaskService from '../../api/task';

export const MarkupState = {
    ABSENT: 0.0,
    POSSIBLE: 0.5,
    DEFINITE: 1.0
};

export const SubmissionState = {
    UNSUBMITTED: 'unsubmitted',
    SUBMITTING: 'submitting',
    SUBMITTED: 'submitted',
    FAILED: 'failed',
    FINISHED: 'finished'
};

function initialState() {
    return {
        annotation: null,
        study: null,
        image: null,
        flagStatus: 'ok',
        startTime: null,
        showReview: false,
        markupState: MarkupState.DEFINITE,
        responses: {},
        markups: {},
        activeFeatureId: null,
        submissionState: SubmissionState.UNSUBMITTED
    };
}

export default {
    namespaced: true,
    state: initialState(),
    getters: {
        questions(state) {
            return state.study ? state.study.questions : [];
        },
        features(state) {
            return state.study ? state.study.features : [];
        },
        markedupFeatureIds(state) {
            return Object.keys(state.markups);
        }
    },
    mutations: {
        resetState(state) {
            state = Object.assign(state, initialState());
        },
        setAnnotation(state, annotation) {
            state.annotation = annotation;
        },
        setStudy(state, study) {
            state.study = study;
        },
        setImage(state, image) {
            state.image = image;
        },
        setFlagStatus(state, data) {
            state.flagStatus = data;
        },
        setStartTime(state, data) {
            state.startTime = data;
        },
        setShowReview(state, data) {
            state.showReview = data;
        },
        setMarkupState(state, data) {
            state.markupState = data;
        },
        setResponses(state, data) {
            state.responses = data;
        },
        setResponse(state, { questionId, response }) {
            state.responses[questionId] = response;
        },
        setMarkups(state, data) {
            state.markups = data;
        },
        setMarkup(state, { featureId, values }) {
            if (values) {
                Vue.set(state.markups, featureId, values);
            } else {
                Vue.delete(state.markups, featureId);
            }
        },
        setActiveFeatureId(state, data) {
            state.activeFeatureId = data;
        },
        setSubmissionState(state, data) {
            state.submissionState = data;
        }
    },
    actions: {
        getNextAnnotation({ state, dispatch, commit }, { studyId }) {
            TaskService.getNextAnnotation(studyId)
                .done((resp) => {
                    commit('setAnnotation', resp);
                    commit('setStartTime', Date.now());
                    dispatch('getImage', {id: state.annotation.imageId});
                })
                .fail((resp) => {
                    if (resp.status === 404) {
                        commit('setSubmissionState', SubmissionState.FINISHED);
                    }
                });
        },
        getStudy({ commit }, { id }) {
            StudyService.get(id)
                .done((resp) => commit('setStudy', resp));
        },
        getImage({ commit }, { id }) {
            ImageService.get(id)
                .done((resp) => commit('setImage', resp));
        },
        submitAnnotation({ state, commit }) {
            commit('setSubmissionState', SubmissionState.SUBMITTING);

            // Submit only responses to questions that user answered
            const responses = _.omit(state.responses, (value) => _.isNull(value));
            const stopTime = Date.now();

            const annotation = {
                status: state.flagStatus,
                imageId: state.image._id,
                startTime: state.startTime,
                stopTime: stopTime,
                responses: responses,
                markups: state.markups
            };

            AnnotationService.submit(state.annotation._id, annotation)
                .done(() => commit('setSubmissionState', SubmissionState.SUBMITTED))
                .fail(() => commit('setSubmissionState', SubmissionState.FAILED));
        }
    }
};
