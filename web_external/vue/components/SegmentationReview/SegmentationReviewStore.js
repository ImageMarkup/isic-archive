/**
 * Segmentation review Vuex store.
 */

import DatasetService from '../../api/dataset';
import SegmentationService from '../../api/segmentation';
import TaskService from '../../api/task';

export const WorkflowState = {
    // Awaiting user interaction
    IDLE: 'idle',
    // Submitting segmentation review
    SUBMITTING: 'submitting',
    // Loading next image and segmentations
    LOADING: 'loading',
    // Segmentation review is complete
    FINISHED: 'finished'
};

function initialState() {
    return {
        dataset: null,
        image: null,
        segmentations: [],
        activeSegmentationIndex: -1,
        workflowState: WorkflowState.IDLE
    };
}

export default {
    namespaced: true,
    state: initialState(),
    getters: {
        activeSegmentation(state) {
            if (state.activeSegmentationIndex < 0) {
                return null;
            }
            return state.segmentations[state.activeSegmentationIndex];
        }
    },
    mutations: {
        resetState(state) {
            state = Object.assign(state, initialState());
        },
        setSegmentations(state, data) {
            state.segmentations = data;
        },
        setDataset(state, dataset) {
            state.dataset = dataset;
        },
        setImage(state, image) {
            state.image = image;
        },
        setActiveSegmentationIndex(state, index) {
            state.activeSegmentationIndex = index;
        },
        setWorkflowState(state, data) {
            state.workflowState = data;
        }
    },
    actions: {
        loadDataset({ dispatch, commit }, { id }) {
            // Reset state
            commit('setDataset', null);
            commit('setImage', null);
            commit('setSegmentations', []);
            commit('setActiveSegmentationIndex', -1);
            commit('setWorkflowState', WorkflowState.LOADING);

            // Fetch dataset
            DatasetService.get(id)
                .done((resp) => {
                    commit('setDataset', resp);
                })
                .fail((resp) => {
                    // TODO: Handle error
                });

            // Fetch image with segmentations to review
            dispatch('loadNextImage', {datasetId: id});
        },
        loadNextImage({ state, dispatch, commit }, { datasetId }) {
            commit('setWorkflowState', WorkflowState.LOADING);

            TaskService.getNextImageForSegmentation(datasetId)
                .done((resp) => {
                    commit('setImage', resp);
                    dispatch('loadSegmentationsForImage', {id: resp['_id']});
                })
                .fail((resp) => {
                    if (resp.status === 404) {
                        commit('setWorkflowState', WorkflowState.FINISHED);
                    } else {
                        // TODO: Handle error
                    }
                });
        },
        loadSegmentationsForImage({ commit }, { id }) {
            SegmentationService.getSegmentationsForImage(id)
                .done((resp) => {
                    commit('setSegmentations', resp);
                    if (resp.length > 0) {
                        commit('setActiveSegmentationIndex', 0);
                    }

                    commit('setWorkflowState', WorkflowState.IDLE);
                })
                .fail((resp) => {
                    // TODO: Handle error
                });
        },
        submitReview({ state, dispatch, commit }, { segmentationId, approved }) {
            commit('setWorkflowState', WorkflowState.SUBMITTING);

            SegmentationService.submitReview(segmentationId, approved)
                .done((resp) => {
                    const newActiveSegmentationIndex = state.activeSegmentationIndex + 1;
                    if (newActiveSegmentationIndex >= state.segmentations.length) {
                        // Fetch next with segmentations to review
                        dispatch('loadNextImage', {datasetId: state.dataset._id});
                    } else {
                        commit('setActiveSegmentationIndex', newActiveSegmentationIndex);
                        commit('setWorkflowState', WorkflowState.IDLE);
                    }
                })
                .fail((resp) => {
                    // TODO: Handle error
                    commit('setWorkflowState', WorkflowState.IDLE);
                });
        }
    }
};
