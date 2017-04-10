import _ from 'underscore';

import {getCurrentUser, setCurrentUser} from 'girder/auth';
import events from 'girder/events';

import router from './router';
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

import CreateDatasetRequestView from './Datasets/CreateDatasetRequestView';
import DatasetCollection from './collections/DatasetCollection';
function navigateToIfCanCreateDataset(View, settings) {
    // Users must:
    //  (1) Be registered
    //  (2) Accept the TOS
    //  (3) Request and receive create dataset access
    // before being able to see the create dataset view
    var currentUser = getCurrentUser();
    if (!currentUser) {
        // Anonymous users should not be here, so route to home page
        router.navigate('', {trigger: true});
    } else if (!currentUser.canAcceptTerms()) {
        navigateTo(TermsAcceptanceView);
    } else if (!DatasetCollection.canCreate()) {
        navigateTo(CreateDatasetRequestView);
    } else {
        navigateTo(View, settings);
    }
}

// Front page
import FrontPageView from './Front/FrontPageView';
router.route('', 'index', function () {
    navigateTo(FrontPageView);
});
router.route('forum', 'forum', function () {
    window.location.replace('http://forum.isic-archive.com');
});

// User management
import UserAccountView from 'girder/views/body/UserAccountView';
import eventStream from 'girder/utilities/EventStream';
import { restRequest } from 'girder/rest';
router.route('useraccount/:id/:tab', 'accountTab', function (id, tab) {
    UserAccountView.fetchAndInit(id, tab);
});
router.route('users', 'users', function (id, tab) {
    // This is routed to when UserAccountView wants to return, so redirect home
    router.navigate('', {trigger: true});
});
router.route('useraccount/:id/token/:token', 'accountToken', function (id, token) {
    // This allows reset password links to work
    // TODO: push this logic into the user model in upstream Girder
    restRequest({
        path: 'user/password/temporary/' + id,
        type: 'GET',
        data: {token: token},
        error: null
    }).done(_.bind(function (resp) {
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
    }, this)).error(_.bind(function () {
        router.navigate('', {trigger: true});
    }, this));
});
import InviteUserView from './User/InviteUserView';
router.route('user/invite', 'inviteUser', function () {
    var currentUser = getCurrentUser();
    if (currentUser && currentUser.canAdminStudy()) {
        navigateTo(InviteUserView);
    } else {
        router.navigate('', {trigger: true});
    }
});
import RsvpUserView from './User/RsvpUserView';
import {showAlertDialog} from './common/utilities';
router.route('user/:id/rsvp/:token', 'rsvpUser', function (id, token) {
    UserModel
        .temporaryTokenLogin(id, token)
        .done(function (resp) {
            events.trigger('g:navigateTo', RsvpUserView, {
                user: getCurrentUser(),
                token: token
            });
        })
        .fail(function (resp) {
            showAlertDialog({
                text: '<h4>Error loading user from token</h4><br>' + _.escape(resp.responseJSON.message),
                escapedHtml: true
            });
            router.navigate('', {trigger: true});
        });
});

// Legal
import MedicalDisclaimerView from './Legal/MedicalDisclaimerView';
router.route('medicalDisclaimer', 'medicalDisclaimer', function () {
    navigateTo(MedicalDisclaimerView);
});
import PrivacyPolicyView from './Legal/PrivacyPolicyView';
router.route('privacyPolicy', 'privacyPolicy', function () {
    navigateTo(PrivacyPolicyView);
});
import TermsOfUseView from './Legal/TermsOfUseView';
router.route('termsOfUse', 'termsOfUse', function () {
    navigateTo(TermsOfUseView);
});

// Dataset
import DatasetsView from './Datasets/DatasetsView';
router.route('dataset', 'dataset', function () {
    navigateToIfTermsAccepted(DatasetsView);
});
import CreateDatasetView from './Datasets/CreateDatasetView';
router.route('dataset/create', 'createDataset', function () {
    navigateToIfCanCreateDataset(CreateDatasetView);
});
import ApplyMetadataView from './Datasets/ApplyMetadataView';
router.route('dataset/:id/metadata/apply', 'applyMetadata', function (id) {
    // Fetch the dataset, then navigate to the view
    var dataset = new DatasetModel({_id: id})
        .once('g:fetched', function () {
            navigateToIfCanCreateDataset(ApplyMetadataView, {
                dataset: dataset
            });
        }, this)
        .once('g:error', function () {
            router.navigate('', {trigger: true});
        }, this)
        .fetch();
});
import RegisterMetadataView from './Datasets/RegisterMetadataView';
router.route('dataset/:id/metadata/register', 'registerMetadata', function (id) {
    // Fetch the dataset, then navigate to the view
    var dataset = new DatasetModel({_id: id})
        .once('g:fetched', function () {
            navigateToIfCanCreateDataset(RegisterMetadataView, {
                dataset: dataset
            });
        }, this)
        .once('g:error', function () {
            router.navigate('', {trigger: true});
        }, this)
        .fetch();
});

// Image
import ImagesView from './ImagesGallery/ImagesView';
router.route('images', 'images', function () {
    navigateToIfTermsAccepted(ImagesView);
});

// Featureset
import FeaturesetsView from './Featuresets/FeaturesetsView';
router.route('featuresets', 'featuresets', function () {
    navigateToIfTermsAccepted(FeaturesetsView);
});

// Study
import StudiesView from './Studies/StudiesView';
router.route('studies', 'studies', function () {
    navigateToIfTermsAccepted(StudiesView);
});
import CreateStudyView from './Studies/CreateStudyView';
import StudyCollection from './collections/StudyCollection';
router.route('createStudy', 'createStudy', function () {
    // Route to index if user isn't a study administrator
    if (StudyCollection.canCreate()) {
        navigateTo(CreateStudyView);
    } else {
        router.navigate('', {trigger: true});
    }
});
import StudyResultsView from './StudyResults/StudyResultsView';
router.route('studyResults', 'studyResults', function () {
    navigateToIfTermsAccepted(StudyResultsView);
});

// Task
import TasksView from './Tasks/TasksView';
router.route('tasks', 'tasks', function () {
    navigateToIfTermsAccepted(TasksView);
});
