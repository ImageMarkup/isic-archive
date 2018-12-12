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
        stopTime: null,
        showReview: false,
        markupState: MarkupState.DEFINITE,
        responses: {},
        markups: {},
        activeFeatureId: null,
        submissionState: SubmissionState.UNSUBMITTED,
        log: []
    };
}

function logEvent(state, type, detail) {
    state.log.push({
        'type': type,
        'time': new Date().toISOString(),
        'detail': detail
    });
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
            logEvent(state, 'flag', {
                'flag': state.flagStatus
            });
        },
        setStartTime(state, data) {
            state.startTime = data;
            logEvent(state, 'annotation_start', {});
        },
        setStopTime(state, data) {
            state.stopTime = data;
            logEvent(state, 'annotation_stop', {});
        },
        setShowReview(state, data) {
            state.showReview = data;

            const eventType = state.showReview ? 'annotation_edit_stop' : 'annotation_edit_resume';
            logEvent(state, eventType, {});
        },
        setMarkupState(state, data) {
            state.markupState = data;
        },
        setResponse(state, { questionId, response }) {
            if (response) {
                Vue.set(state.responses, questionId, response);
                logEvent(state, 'response_set', {
                    'questionId': questionId,
                    'response': state.responses[questionId]
                });
            } else {
                Vue.delete(state.responses, questionId);
                logEvent(state, 'response_clear', {
                    'questionId': questionId
                });
            }
        },
        setMarkup(state, { featureId, values }) {
            if (values) {
                Vue.set(state.markups, featureId, values);
                logEvent(state, 'markup_set', {
                    'featureId': featureId
                });
            } else {
                Vue.delete(state.markups, featureId);
                logEvent(state, 'markup_clear', {
                    'featureId': featureId
                });
            }
        },
        setActiveFeatureId(state, data) {
            state.activeFeatureId = data;
            if (data !== null) {
                // Don't log on deactivation (that's handled by setMarkup)
                logEvent(state, 'markup_select', {
                    'featureId': data
                });
            }
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
                    commit('setStartTime', new Date());
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
        resetResponses({ state, commit }) {
            _.each(state.responses, (response, questionId) => {
                commit('setResponse', {
                    questionId,
                    response: null
                });
            });
        },
        resetMarkups({ state, commit }) {
            _.each(state.markups, (values, featureId) => {
                commit('setMarkup', {
                    featureId,
                    values: null
                });
            });
        },
        submitAnnotation({ state, commit }) {
            commit('setSubmissionState', SubmissionState.SUBMITTING);
            commit('setStopTime', new Date());

            // Submit only responses to questions that user answered
            const responses = _.omit(state.responses, (value) => _.isNull(value));

            const annotation = {
                status: state.flagStatus,
                imageId: state.image._id,
                startTime: state.startTime.getTime(),
                stopTime: state.stopTime.getTime(),
                responses: responses,
                markups: state.markups,
                log: state.log
            };

            AnnotationService.submit(state.annotation._id, annotation)
                .done(() => commit('setSubmissionState', SubmissionState.SUBMITTED))
                .fail(() => commit('setSubmissionState', SubmissionState.FAILED));
        }
    }
};
