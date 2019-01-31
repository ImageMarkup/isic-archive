/* eslint-disable import/first, import/order */

import _ from 'underscore';

import {getCurrentUser, setCurrentToken} from '@girder/core/auth';
import events from '@girder/core/events';

import router from './router';
import VueComponentView from './vueComponentView';
import DatasetModel from './models/DatasetModel';
import UserModel from './models/UserModel';

function navigateTo(View, settings) {
    events.trigger('g:navigateTo', View, settings, null);
}

import TermsAcceptanceView from './Legal/TermsAcceptanceView';
function navigateToIfTermsAccepted(View, settings) {
    if (!UserModel.currentUserCanAcceptTerms()) {
        navigateTo(TermsAcceptanceView);
    } else {
        navigateTo(View, settings);
    }
}

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

import CreateDatasetRequestView from './Datasets/CreateDatasetRequestView';
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
import FrontPageView from './Front/FrontPageView';
router.route('', 'index', () => {
    navigateTo(FrontPageView);
});

// Literature page
import LiteratureView from './Literature/LiteratureView';
router.route('literature', 'literature', () => {
    navigateTo(LiteratureView);
});

// User management
import UserAccountView from '@girder/core/views/body/UserAccountView';
router.route('useraccount/:id/:tab', 'accountTab', (id, tab) => {
    UserAccountView.fetchAndInit(id, tab);
});
router.route('users', 'users', (id, tab) => {
    // This is routed to when UserAccountView wants to return, so redirect home
    router.navigate('', {trigger: true});
});
router.route('useraccount/:id/token/:token', 'accountToken', (id, token) => {
    // This allows reset password links to work
    UserModel.fromTemporaryToken(id, token)
        .done((resp) => {
            // TODO: Move this upstream
            setCurrentToken(resp.authToken.token);

            events.trigger('g:navigateTo', UserAccountView, {
                user: getCurrentUser(),
                tab: 'password',
                temporary: token
            });
        })
        .fail(() => {
            router.navigate('', {trigger: true});
        });
});
import InviteUserView from './User/InviteUserView';
router.route('user/invite', 'inviteUser', () => {
    let currentUser = getCurrentUser();
    if (currentUser && currentUser.canAdminStudy()) {
        navigateTo(InviteUserView);
    } else {
        router.navigate('', {trigger: true});
    }
});
import RsvpUserView from './User/RsvpUserView';
import {showAlertDialog} from './common/utilities';
router.route('user/:id/rsvp/:token', 'rsvpUser', (id, token) => {
    UserModel.fromTemporaryToken(id, token)
        .done((resp) => {
            // TODO: Move this upstream
            setCurrentToken(resp.authToken.token);

            events.trigger('g:navigateTo', RsvpUserView, {
                user: getCurrentUser(),
                token: token
            });
        })
        .fail((resp) => {
            showAlertDialog({
                text: `<h4>Error loading user from token</h4><br>${_.escape(resp.responseJSON.message)}`,
                escapedHtml: true
            });
            router.navigate('', {trigger: true});
        });
});

// Legal
import MedicalDisclaimerView from './Legal/MedicalDisclaimerView';
router.route('medicalDisclaimer', 'medicalDisclaimer', () => {
    navigateTo(MedicalDisclaimerView);
});
import PrivacyPolicyView from './Legal/PrivacyPolicyView';
router.route('privacyPolicy', 'privacyPolicy', () => {
    navigateTo(PrivacyPolicyView);
});
import TermsOfUseView from './Legal/TermsOfUseView';
router.route('termsOfUse', 'termsOfUse', () => {
    navigateTo(TermsOfUseView);
});

// Dataset
import DatasetsView from './Datasets/DatasetsView';
router.route('dataset', 'dataset', () => {
    navigateToIfTermsAccepted(DatasetsView);
});
import CreateDatasetView from './Datasets/CreateDatasetView';
router.route('dataset/create', 'createDataset', () => {
    navigateToIfCanCreateDataset(CreateDatasetView);
});
import UploadBatchView from './Datasets/UploadBatchView';
router.route('dataset/upload/batch', 'uploadBatch', () => {
    navigateToIfCanCreateDataset(UploadBatchView);
});
import ApplyMetadataView from './Datasets/ApplyMetadataView';
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
import RegisterMetadataView from './Datasets/RegisterMetadataView';
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
import UploadImage from './Datasets/UploadImage.vue';
router.route('dataset/upload/image', 'uploadImage', () => {
    navigateToIfCanCreateDataset(VueComponentView, {
        component: UploadImage
    });
});

// Image
import ImagesView from './ImagesGallery/ImagesView';
router.route('images', 'images', () => {
    navigateToIfTermsAccepted(ImagesView);
});

// Study
import StudiesView from './Studies/StudiesView';
router.route('studies', 'studies', () => {
    navigateToIfTermsAccepted(StudiesView);
});
import CreateStudyView from './Studies/CreateStudyView';
import StudyCollection from './collections/StudyCollection';
router.route('createStudy', 'createStudy', () => {
    // Route to index if user isn't a study administrator
    if (StudyCollection.canCreate()) {
        navigateTo(CreateStudyView);
    } else {
        router.navigate('', {trigger: true});
    }
});
import StudyResultsView from './StudyResults/StudyResultsView';
router.route('studyResults', 'studyResults', () => {
    navigateToIfTermsAccepted(StudyResultsView);
});

// Task
import TasksView from './Tasks/TasksView';
router.route('tasks', 'tasks', () => {
    navigateToIfLoggedIn(TasksView);
});
import DatasetReview from './vue/components/DatasetReview/DatasetReview.vue';
router.route('tasks/review/:id', 'review', (id) => {
    navigateToIfLoggedIn(VueComponentView, {
        component: DatasetReview,
        props: {
            datasetId: id
        }
    });
});
import SegmentationReview from './vue/components/SegmentationReview/SegmentationReview.vue';
router.route('tasks/segmentationreview/:id', 'segmentationReview', (id) => {
    navigateToIfLoggedIn(VueComponentView, {
        component: SegmentationReview,
        props: {
            datasetId: id
        }
    });
});
import AnnotationTool from './vue/components/AnnotationTool/AnnotationTool.vue';
router.route('tasks/annotate/:id', 'annotate', (id) => {
    navigateToIfLoggedIn(VueComponentView, {
        component: AnnotationTool,
        props: {
            studyId: id
        }
    });
});
