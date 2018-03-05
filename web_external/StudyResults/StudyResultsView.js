import Backbone from 'backbone';
import $ from 'jquery';
import _ from 'underscore';

import {getApiRoot} from 'girder/rest';

import AnnotationCollection from '../collections/AnnotationCollection';
import ImageCollection from '../collections/ImageCollection';
import StudyCollection from '../collections/StudyCollection';
import UserCollection from '../collections/UserCollection';
import AnnotationModel from '../models/AnnotationModel';
import FeaturesetModel from '../models/FeaturesetModel';
import ImageModel from '../models/ImageModel';
import StudyModel from '../models/StudyModel';
import UserModel from '../models/UserModel';
import ImageViewerWidget from '../common/Viewer/ImageViewerWidget';
import View from '../view';

import StudyResultsImageHeaderPageTemplate from './studyResultsImageHeaderPage.pug';
import './studyResultsImageHeaderPage.styl';
import StudyResultsSelectStudyPageTemplate from './studyResultsSelectStudyPage.pug';
import './studyResultsSelectStudyPage.styl';
import StudyResultsStudyDetailPageTemplate from './studyResultsStudyDetailPage.pug';
import './studyResultsStudyDetailPage.styl';
import StudyResultsSelectImagePageTemplate from './studyResultsSelectImagePage.pug';
import './studyResultsSelectImagePage.styl';
import StudyResultsSelectUsersPageTemplate from './studyResultsSelectUsersPage.pug';
import './studyResultsSelectUsersPage.styl';
import StudyResultsSelectLocalFeaturesPageTemplate from './studyResultsSelectLocalFeaturesPage.pug';
import './studyResultsSelectLocalFeaturesPage.styl';
import StudyResultsGlobalFeaturesTableTemplate from './studyResultsGlobalFeaturesTable.pug';
import StudyResultsGlobalFeaturesPageTemplate from './studyResultsGlobalFeaturesPage.pug';
import './studyResultsGlobalFeaturesPage.styl';
import StudyResultsFeatureImagePageTemplate from './studyResultsFeatureImagePage.pug';
import StudyResultsLocalFeaturesPageTemplate from './studyResultsLocalFeaturesPage.pug';
import './studyResultsLocalFeaturesPage.styl';
import StudyResultsImagePageTemplate from './studyResultsImagePage.pug';
import './studyResultsImagePage.styl';
import StudyResultsPageTemplate from './studyResultsPage.pug';
import './studyResultsPage.styl';

// Model for a feature
const FeatureModel = Backbone.Model.extend({
    name: function () {
        return this.get('name');
    }
});

// Model for a feature image
const FeatureImageModel = Backbone.Model.extend({
});

// Model for a global feature result
const GlobalFeatureResultModel = Backbone.Model.extend({
    name: function () {
        return this.get('name');
    }
});

// Collection of feature models
const FeatureCollection = Backbone.Collection.extend({
    model: FeatureModel,

    // Update collection from an array of features of the form:
    // { 'id': id, 'name': [name1, name2, ...] }
    update: function (features) {
        let models = _.map(features, (feature) => {
            let featureId = feature['id'];
            let featureNames = feature['name'];
            let model = new FeatureModel({
                id: featureId,
                name: featureNames.join(', ')
            });
            return model;
        });
        this.reset(models);
    }
});

// Header view for collection of images
const StudyResultsImageHeaderView = View.extend({
    /**
     * @param {ImageCollection} settings.collection
     * @param {StudyModel} settings.study
     */
    initialize: function (settings) {
        this.study = settings.study;

        this.listenTo(this.collection, 'reset', this.render);

        this.render();
    },

    render: function () {
        this.$el.html(StudyResultsImageHeaderPageTemplate({
            hasStudy: !_.isUndefined(this.study.id),
            numImages: this.collection.size()
        }));

        return this;
    }
});

// View for a collection of studies in a select tag
const StudyResultsSelectStudyView = View.extend({
    events: {
        'change': 'studyChanged',
        'click .isic-study-results-select-study-details-button': 'showDetails'
    },

    /**
     * @param {StudyCollection} settings.collection
     */
    initialize: function (settings) {
        this.listenTo(this.collection, 'reset', this.render);

        this.render();
    },

    studyChanged: function () {
        this.trigger('changed', this.$('select').val());

        // Enable study details button
        this.$('.isic-study-results-select-study-details-button').girderEnable(true);
    },

    showDetails: function () {
        let studyId = this.$('select').val();
        if (!studyId) {
            return;
        }

        this.trigger('showStudyDetails', studyId);
    },

    render: function () {
        // Destroy previous select2
        let select = this.$('#isic-study-results-select-study-select');
        select.select2('destroy');

        this.$el.html(StudyResultsSelectStudyPageTemplate({
            models: this.collection.toArray()
        }));

        // Set up select box
        let placeholder = 'Select a study...';
        if (!this.collection.isEmpty()) {
            placeholder += ` (${this.collection.length} available)`;
        }
        select = this.$('#isic-study-results-select-study-select');
        select.select2({
            placeholder: placeholder
        });
        select.focus();

        return this;
    }
});

// Modal view for study details
const StudyResultsStudyDetailsView = View.extend({
    /**
     * @param {StudyModel} settings.model
     */
    initialize: function (settings) {
    },

    render: function () {
        let hasStudy = this.model.has('name');

        this.$el.html(StudyResultsStudyDetailPageTemplate({
            model: this.model,
            hasStudy: hasStudy
        })).girderModal(this);

        return this;
    }
});

// View for a collection of images
const StudyResultsSelectImageView = View.extend({
    events: {
        'click .isic-study-results-select-image-image-container': 'imageSelected'
    },

    /**
     * @param {ImageCollection} settings.collection
     */
    initialize: function (settings) {
        this.listenTo(this.collection, 'reset', this.render);

        this.render();
    },

    imageSelected: function (event) {
        event.preventDefault();

        // currentTarget is the element that the event has bubbled up to
        let target = $(event.currentTarget);

        this.$('.isic-study-results-select-image-image-container').removeClass('active');
        target.addClass('active');

        this.trigger('changed', target.data('imageId'));
    },

    render: function () {
        this.$el.html(StudyResultsSelectImagePageTemplate({
            models: this.collection.toArray(),
            apiRoot: getApiRoot()
        }));

        return this;
    }
});

// View for a collection of users in a select tag
const StudyResultsSelectUsersView = View.extend({
    events: {
        'change': 'userChanged'
    },

    /**
     * @param {UserCollection} settings.collection
     */
    initialize: function (settings) {
        this.listenTo(this.collection, 'reset', this.render);

        this.render();
    },

    userChanged: function () {
        this.trigger('changed', this.$('select').val());
    },

    render: function () {
        // Destroy previous select2
        let select = this.$('#isic-study-results-select-users-select');
        select.select2('destroy');

        this.$el.html(StudyResultsSelectUsersPageTemplate({
            models: this.collection.toArray()
        }));

        // Set up select box
        let placeholder = 'No users available';
        if (!this.collection.isEmpty()) {
            placeholder = `Select an annotator... (${this.collection.length} available)`;
        }
        select = this.$('#isic-study-results-select-users-select');
        select.select2({
            placeholder: placeholder
        });

        return this;
    }
});

// View for a collection of local features in a select tag
const StudyResultsSelectLocalFeaturesView = View.extend({
    events: {
        'change': 'featureChanged'
    },

    /**
     * @param {FeatureCollection} settings.collection
     * @param {function} settings.featureAnnotated - A boolean-returning function, taking a featureId parameter.
     */
    initialize: function (settings) {
        this.featureAnnotated = settings.featureAnnotated;

        this.listenTo(this.collection, 'reset', this.render);

        this.render();
    },

    featureChanged: function () {
        this.trigger('changed', this.$('select').val());
    },

    render: function () {
        // Destroy previous select2
        let select = this.$('#isic-study-results-select-local-features-select');
        select.select2('destroy');

        // Create local collection of those features that are annotated
        let collection = this.collection.clone();
        collection.reset(collection.filter((model) => {
            return this.featureAnnotated(model.id);
        }));

        this.$el.html(StudyResultsSelectLocalFeaturesPageTemplate({
            models: collection.toArray()
        }));

        // Set up select box
        let placeholder = 'No features available';
        if (!collection.isEmpty()) {
            placeholder = `Select a feature... (${collection.length} available)`;
        }
        select = this.$('#isic-study-results-select-local-features-select');
        select.select2({
            placeholder: placeholder
        });

        return this;
    }
});

// Collection of global feature result models
const GlobalFeatureResultCollection = Backbone.Collection.extend({
    model: GlobalFeatureResultModel,

    // Update collection from annotation object and feature list
    update: function (annotations, features) {
        let models = _.map(features, (feature) => {
            let featureId = feature['id'];
            let featureNames = feature['name'];
            let model = new GlobalFeatureResultModel({
                id: featureId,
                name: featureNames.join(', ')
            });
            if (annotations && _.has(annotations, featureId)) {
                let featureOptions = _.indexBy(feature['options'], 'id');
                let resultId = annotations[featureId];
                let resultName = featureOptions[resultId]['name'];
                model.set('resultId', resultId);
                model.set('resultName', resultName);
            }
            return model;
        });
        this.reset(models);
    }
});

// View for a global feature table
const StudyResultsGlobalFeaturesTableView = View.extend({
    /**
     * @param {GlobalFeatureResultCollection} settings.collection
     */
    initialize: function (settings) {
        this.listenTo(this.collection, 'reset', this.render);
    },

    render: function () {
        this.$el.html(StudyResultsGlobalFeaturesTableTemplate({
            features: this.collection.toArray()
        }));

        return this;
    }
});

// View for the annotation results of global features in a featureset
const StudyResultsGlobalFeaturesView = View.extend({
    /**
     * @param {AnnotationModel} settings.annotation
     * @param {FeaturesetModel} settings.featureset
     */
    initialize: function (settings) {
        this.annotation = settings.annotation;
        this.featureset = settings.featureset;

        this.results = new GlobalFeatureResultCollection();
        this.listenTo(this.featureset, 'change', this.render);
        this.listenTo(this.featureset, 'change', this.updateResults);
        this.listenTo(this.annotation, 'change', this.updateResults);

        this.tableView = new StudyResultsGlobalFeaturesTableView({
            collection: this.results,
            parentView: this
        });

        this.updateResults();
        this.render();
    },

    render: function () {
        this.$el.html(StudyResultsGlobalFeaturesPageTemplate({
            hasGlobalFeatures: !_.isEmpty(this.featureset.get('globalFeatures')),
            featureset: this.featureset
        }));

        this.tableView.setElement(
            this.$('#isic-study-results-global-features-table')).render();

        return this;
    },

    updateResults: function () {
        this.results.update(
            this.annotation.get('responses'),
            this.featureset.get('globalFeatures')
        );
    }
});

// View for a local feature image defined by an annotation and local feature
const StudyResultsFeatureImageView = View.extend({
    /**
     * @param {FeatureImageModel} settings.model
     */
    initialize: function (settings) {
        this.listenTo(this.model, 'change', this.render);
    },

    setVisible: function (visible) {
        if (visible) {
            this.$el.removeClass('hidden');
        } else {
            this.$el.addClass('hidden');
        }
    },

    render: function () {
        let featureId = this.model.get('featureId');
        let annotationId = this.model.get('annotationId');
        let imageUrl = null;
        if (featureId && annotationId) {
            imageUrl = [
                getApiRoot(),
                'annotation', annotationId,
                encodeURIComponent(featureId),
                'render'
            ].join('/') + '?contentDisposition=inline';
        }

        this.$el.html(StudyResultsFeatureImagePageTemplate({
            imageUrl: imageUrl
        }));

        return this;
    }
});

// View to allow selecting a local feature from a featureset and to display an
// image showing the annotation for the feature
const StudyResultsLocalFeaturesView = View.extend({
    /**
     * @param {AnnotationModel} settings.annotation
     * @param {FeaturesetModel} settings.featureset
     * @param {FeatureImageModel} settings.model
     */
    initialize: function (settings) {
        this.annotation = settings.annotation;
        this.featureset = settings.featureset;
        this.featureImageModel = settings.featureImageModel;
        this.features = new FeatureCollection();

        this.listenTo(this.featureset, 'change', this.featuresetChanged);
        this.listenTo(this.annotation, 'change', this.annotationChanged);

        this.selectFeatureView = new StudyResultsSelectLocalFeaturesView({
            collection: this.features,
            featureAnnotated: _.bind(this.featureAnnotated, this),
            parentView: this
        });

        this.listenTo(this.selectFeatureView, 'changed', this.featureChanged);
    },

    featureChanged: function (featureId) {
        this.featureId = featureId;
        this.updateFeatureImageModel();
    },

    updateFeatureImageModel: function () {
        this.featureImageModel.set({
            featureId: this.featureId,
            annotationId: this.featureAnnotated(this.featureId) ? this.annotation.id : null
        });
    },

    render: function () {
        this.$el.html(StudyResultsLocalFeaturesPageTemplate({
            hasLocalFeatures: !_.isEmpty(this.featureset.get('localFeatures')),
            featureset: this.featureset
        }));

        this.selectFeatureView.setElement(
            this.$('#isic-study-results-select-local-feature-container')).render();

        return this;
    },

    updateFeatureCollection: function () {
        delete this.featureId;

        this.features.update(this.featureset.get('localFeatures'));
    },

    featuresetChanged: function () {
        this.updateFeatureCollection();
        this.render();
    },

    annotationChanged: function () {
        this.featureId = null;
        this.updateFeatureImageModel();
        this.render();
    },

    featureAnnotated: function (featureId) {
        if (!featureId || !this.annotation.has('markups')) {
            return false;
        }
        let markups = this.annotation.get('markups');
        return _.has(markups, featureId);
    }
});

// View for an image
const StudyResultsImageView = View.extend({
    /**
     * @param {ImageModel} settings.model
     */
    initialize: function (settings) {
    },

    setVisible: function (visible) {
        if (visible) {
            this.$el.removeClass('hidden');

            this.imageViewerWidget.render();
        } else {
            this.$el.addClass('hidden');
        }
    },

    render: function () {
        this.$el.html(StudyResultsImagePageTemplate({
        }));

        this.imageViewerWidget = new ImageViewerWidget({
            el: this.$('.isic-study-results-image-preview-container'),
            model: this.model,
            parentView: this
        }).render();

        return this;
    }
});

// View for the results of an annotation study
const StudyResultsView = View.extend({
    events: {
        // Update image visibility when image preview tab is activated
        'shown.bs.tab #isic-study-results-image-preview-tab': function (event) {
            this.localFeaturesImageView.setVisible(false);
            this.imageView.setVisible(true);
        },

        // Update image visibility when global features tab is activated
        'shown.bs.tab #isic-study-results-global-features-tab': function (event) {
            this.imageView.setVisible(false);
            this.localFeaturesImageView.setVisible(false);
        },

        // Update image visibility when local features tab is activated
        'shown.bs.tab #isic-study-results-local-features-tab': function (event) {
            this.imageView.setVisible(false);
            this.localFeaturesImageView.setVisible(true);
        }
    },

    initialize: function (settings) {
        this.studies = new StudyCollection();
        this.studies.pageLimit = Number.MAX_SAFE_INTEGER;

        this.images = new ImageCollection();
        this.images.pageLimit = Number.MAX_SAFE_INTEGER;

        this.users = new UserCollection();
        this.users.pageLimit = Number.MAX_SAFE_INTEGER;

        this.study = new StudyModel();
        this.image = new ImageModel();
        this.user = new UserModel();
        this.featureset = new FeaturesetModel();
        this.annotation = new AnnotationModel();
        this.featureImageModel = new FeatureImageModel();

        this.selectStudyView = new StudyResultsSelectStudyView({
            collection: this.studies,
            parentView: this
        });

        this.studyDetailsView = new StudyResultsStudyDetailsView({
            model: this.study,
            parentView: this
        });

        this.imageHeaderView = new StudyResultsImageHeaderView({
            collection: this.images,
            study: this.study,
            parentView: this
        });

        this.selectImageView = new StudyResultsSelectImageView({
            collection: this.images,
            parentView: this
        });

        this.selectUserView = new StudyResultsSelectUsersView({
            collection: this.users,
            parentView: this
        });

        this.globalFeaturesView = new StudyResultsGlobalFeaturesView({
            annotation: this.annotation,
            featureset: this.featureset,
            parentView: this
        });

        this.localFeaturesView = new StudyResultsLocalFeaturesView({
            annotation: this.annotation,
            featureset: this.featureset,
            featureImageModel: this.featureImageModel,
            parentView: this
        });

        this.imageView = new StudyResultsImageView({
            model: this.image,
            parentView: this
        });

        this.localFeaturesImageView = new StudyResultsFeatureImageView({
            model: this.featureImageModel,
            parentView: this
        });

        this.studies.fetch();

        this.listenTo(this.selectStudyView, 'changed', this.studyChanged);
        this.listenTo(this.selectImageView, 'changed', this.imageChanged);
        this.listenTo(this.selectUserView, 'changed', this.userChanged);

        this.listenTo(this.selectStudyView, 'showStudyDetails', this.showStudyDetails);

        this.render();
    },

    studyChanged: function (studyId) {
        this.study.clear();

        this.images.reset();
        this.users.reset();

        this.image.clear();
        this.user.clear();

        this.annotation.clear();
        this.featureset.clear();

        // Hide main and content containers
        this.setMainContainerVisible(false);
        this.setContentContainerVisible(false);

        // Fetch selected study
        this.study
            .set({'_id': studyId})
            .once('g:fetched', () => {
                // Populate images collection
                let imageModels = _.map(this.study.get('images'), (image) => {
                    return new ImageModel(image);
                });
                this.images.reset(imageModels);

                // Populate users collection
                this.users.reset(this.study.users().toArray());

                // Fetch featureset
                let featureset = this.study.featureset();
                featureset
                    .once('g:fetched', () => {
                        this.featureset.set(featureset.toJSON());
                    })
                    .fetch();

                // Show main container
                this.setMainContainerVisible(true);
            })
            .fetch();
    },

    imageChanged: function (imageId) {
        this.image.set('_id', imageId);
        this.annotation.clear();
        this.fetchAnnotation();

        // Show content container
        this.setContentContainerVisible(true);
    },

    userChanged: function (userId) {
        this.user.set('_id', userId);
        this.annotation.clear();
        this.fetchAnnotation();
    },

    showStudyDetails: function (studyId) {
        this.studyDetailsView.render();
    },

    fetchAnnotation: function () {
        if (!this.image.id ||
            !this.user.id) {
            return;
        }

        let annotations = new AnnotationCollection();
        annotations
            .once('g:changed', () => {
                if (!annotations.isEmpty()) {
                    // Fetch annotation detail
                    this.annotation.set(annotations.first().toJSON()).fetch();
                }
            })
            .fetch({
                studyId: this.study.id,
                userId: this.user.id,
                imageId: this.image.id
            });
    },

    render: function () {
        this.$el.html(StudyResultsPageTemplate());

        this.selectStudyView.setElement(
            this.$('#isic-study-results-select-study-container')).render();
        this.studyDetailsView.setElement(
            $('#g-dialog-container'));
        this.imageHeaderView.setElement(
            this.$('#isic-study-results-select-image-header')).render();
        this.selectImageView.setElement(
            this.$('#isic-study-results-select-image-container')).render();
        this.selectUserView.setElement(
            this.$('#isic-study-results-select-user-container')).render();
        this.globalFeaturesView.setElement(
            this.$('#isic-study-results-global-features-container')).render();
        this.localFeaturesView.setElement(
            this.$('#isic-study-results-local-features-container')).render();
        this.imageView.setElement(
            this.$('#isic-study-results-image-preview-container')).render();
        this.localFeaturesImageView.setElement(
            this.$('#isic-study-results-local-features-image-container')).render();

        return this;
    },

    setElementVisible: function (element, visible) {
        if (visible) {
            element.removeClass('hidden');
        } else {
            element.addClass('hidden');
        }
    },

    setMainContainerVisible: function (visible) {
        let element = this.$('#isic-study-results-main-container');
        this.setElementVisible(element, visible);
    },

    setContentContainerVisible: function (visible) {
        this.setElementVisible(this.$('#isic-study-results-main-content'), visible);
        this.setElementVisible(this.$('#isic-study-results-select-user-container'), visible);
    }

});

export default StudyResultsView;
