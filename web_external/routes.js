/* eslint-disable import/first, import/order */

import _ from 'underscore';

import {getCurrentUser, setCurrentUser} from 'girder/auth';
import {AccessType} from 'girder/constants';
import events from 'girder/events';

import router from './router';
import VueComponentView from './vueComponentView';
import DatasetCollection from './collections/DatasetCollection';
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
import UserAccountView from 'girder/views/body/UserAccountView';
import eventStream from 'girder/utilities/EventStream';
import { restRequest } from 'girder/rest';
router.route('useraccount/:id/:tab', 'accountTab', (id, tab) => {
    UserAccountView.fetchAndInit(id, tab);
});
router.route('users', 'users', (id, tab) => {
    // This is routed to when UserAccountView wants to return, so redirect home
    router.navigate('', {trigger: true});
});
router.route('useraccount/:id/token/:token', 'accountToken', (id, token) => {
    // This allows reset password links to work
    // TODO: push this logic into the user model in upstream Girder
    restRequest({
        url: `user/password/temporary/${id}`,
        data: {token: token},
        error: null
    }).done((resp) => {
        resp.user.token = resp.authToken.token;
        eventStream.close();
        setCurrentUser(new UserModel(resp.user));
        eventStream.open();
        events.trigger('g:login-changed');
        events.trigger('g:navigateTo', UserAccountView, {
            user: getCurrentUser(),
            tab: 'password',
            temporary: token
        });
    }).fail(() => {
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
    UserModel
        .temporaryTokenLogin(id, token)
        .done((resp) => {
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
    // Fetch dataset for which the user has write access, then navigate to the view
    let datasets = new DatasetCollection();
    datasets
        .fetch({
            limit: 0
        })
        .done((resp) => {
            datasets.reset(
                _.filter(resp, (dataset) => {
                    return dataset['_accessLevel'] >= AccessType.WRITE;
                })
            );
            navigateToIfCanCreateDataset(VueComponentView, {
                component: UploadImage,
                props: {
                    datasets: datasets.toArray()
                }
            });
        })
        .fail(() => {
            router.navigate('', {trigger: true});
        });
});

// Image
import ImagesView from './ImagesGallery/ImagesView';
router.route('images', 'images', () => {
    navigateToIfTermsAccepted(ImagesView);
});

// Featureset
import FeaturesetsView from './Featuresets/FeaturesetsView';
router.route('featuresets', 'featuresets', () => {
    navigateToIfTermsAccepted(FeaturesetsView);
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
