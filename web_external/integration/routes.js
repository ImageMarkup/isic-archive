/* eslint-disable import/first, import/order */

import {getCurrentUser} from 'girder/auth';
import events from 'girder/events';

import router from '../router';
import VueComponentView from '../vueComponentView';
import DatasetModel from '../models/DatasetModel';

function navigateTo(View, settings) {
    events.trigger('g:navigateTo', View, settings, null);
}

import TermsAcceptanceView from '../Legal/TermsAcceptanceView';
function navigateToIfLoggedIn(View, settings) {
    let currentUser = getCurrentUser();
    if (!currentUser) {
        events.trigger('g:loginUi');
    } else if (!currentUser.canAcceptTerms()) {
        navigateTo(TermsAcceptanceView);
    } else {
        navigateTo(View, settings);
    }
}

import CreateDatasetRequestView from '../Datasets/CreateDatasetRequestView';
function navigateToIfCanCreateDataset(View, settings) {
    // Users must:
    //  (1) Be logged in
    //  (2) Accept the TOS
    //  (3) Request and receive create dataset access
    // before being able to see the create dataset view
    let currentUser = getCurrentUser();
    if (!currentUser) {
        events.trigger('g:loginUi');
    } else if (!currentUser.canAcceptTerms()) {
        navigateTo(TermsAcceptanceView);
    } else if (!DatasetModel.canCreate()) {
        navigateTo(CreateDatasetRequestView);
    } else {
        navigateTo(View, settings);
    }
}

// Front page
router.route('', 'index', () => {
    window.location.replace('https://www.isic-archive.com/');
});

// Old routes which may still be navigated to by views
router.route('tasks', 'tasks', () => {
    router.navigate('', {trigger: true, replace: true});
});
router.route('dataset', 'dataset', () => {
    router.navigate('', {trigger: true, replace: true});
});

// Literature page
import LiteratureView from '../Literature/LiteratureView';
router.route('literature', 'literature', () => {
    navigateTo(LiteratureView);
});

// Dataset
import UploadBatchView from '../Datasets/UploadBatchView';
router.route('dataset/upload/batch', 'uploadBatch', () => {
    navigateToIfCanCreateDataset(UploadBatchView);
});
import ApplyMetadataView from '../Datasets/ApplyMetadataView';
router.route('dataset/:id/metadata/apply', 'applyMetadata', (id) => {
    // Fetch the dataset, then navigate to the view
    let dataset = new DatasetModel({_id: id})
        .once('g:fetched', () => {
            navigateToIfCanCreateDataset(ApplyMetadataView, {
                dataset: dataset
            });
        })
        .once('g:error', () => {
            router.navigate('', {trigger: true});
        });
    dataset.fetch();
});
import RegisterMetadataView from '../Datasets/RegisterMetadataView';
router.route('dataset/:id/metadata/register', 'registerMetadata', (id) => {
    // Fetch the dataset, then navigate to the view
    let dataset = new DatasetModel({_id: id})
        .once('g:fetched', () => {
            navigateToIfCanCreateDataset(RegisterMetadataView, {
                dataset: dataset
            });
        })
        .once('g:error', () => {
            router.navigate('', {trigger: true});
        });
    dataset.fetch();
});

// Task
import DatasetReview from '../vue/components/DatasetReview/DatasetReview.vue';
router.route('tasks/review/:id', 'review', (id) => {
    navigateToIfLoggedIn(VueComponentView, {
        component: DatasetReview,
        props: {
            datasetId: id
        }
    });
});
import SegmentationReview from '../vue/components/SegmentationReview/SegmentationReview.vue';
router.route('tasks/segmentationreview/:id', 'segmentationReview', (id) => {
    navigateToIfLoggedIn(VueComponentView, {
        component: SegmentationReview,
        props: {
            datasetId: id
        }
    });
});
import AnnotationTool from '../vue/components/AnnotationTool/AnnotationTool.vue';
router.route('tasks/annotate/:id', 'annotate', (id) => {
    navigateToIfLoggedIn(VueComponentView, {
        component: AnnotationTool,
        props: {
            studyId: id
        }
    });
});
