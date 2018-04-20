import Backbone from 'backbone';
import $ from 'jquery';
import _ from 'underscore';

import {getApiRoot} from 'girder/rest';

import AnnotationCollection from '../collections/AnnotationCollection';
import ImageCollection from '../collections/ImageCollection';
import StudyCollection from '../collections/StudyCollection';
import UserCollection from '../collections/UserCollection';
import AnnotationModel from '../models/AnnotationModel';
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
import StudyResultsSelectMarkupPageTemplate from './studyResultsSelectMarkupPage.pug';
import './studyResultsSelectMarkupPage.styl';
import StudyResultsResponsesTableTemplate from './studyResultsResponsesTable.pug';
import StudyResultsResponsesPageTemplate from './studyResultsResponsesPage.pug';
import './studyResultsResponsesPage.styl';
import StudyResultsMarkupImagePageTemplate from './studyResultsMarkupImagePage.pug';
import StudyResultsMarkupsPageTemplate from './studyResultsMarkupsPage.pug';
import './studyResultsMarkupsPage.styl';
import StudyResultsImagePageTemplate from './studyResultsImagePage.pug';
import './studyResultsImagePage.styl';
import StudyResultsPageTemplate from './studyResultsPage.pug';
import './studyResultsPage.styl';

// Model for a markup
const MarkupModel = Backbone.Model.extend({
});

// Model for a markup image
const MarkupImageModel = Backbone.Model.extend({
});

// Model for a response
const ResponseModel = Backbone.Model.extend({
});

// Collection of markup models
const MarkupCollection = Backbone.Collection.extend({
    model: MarkupModel,

    // Update collection from an array of markups
    update: function (markups) {
        let models = _.map(_.keys(markups), (markupId) => {
            return new MarkupModel({
                id: markupId
            });
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

// View for a collection of features in a select tag
const StudyResultsSelectMarkupView = View.extend({
    events: {
        'change': 'featureChanged'
    },

    /**
     * @param {MarkupCollection} settings.collection
     */
    initialize: function (settings) {
        this.listenTo(this.collection, 'reset', this.render);

        this.render();
    },

    featureChanged: function () {
        this.trigger('changed', this.$('select').val());
    },

    render: function () {
        // Destroy previous select2
        let select = this.$('#isic-study-results-select-markup-select');
        select.select2('destroy');

        this.$el.html(StudyResultsSelectMarkupPageTemplate({
            markups: this.collection.toArray()
        }));

        // Set up select box
        let placeholder = 'No markups available';
        if (!this.collection.isEmpty()) {
            placeholder = `Select a markup... (${this.collection.length} available)`;
        }
        select = this.$('#isic-study-results-select-markup-select');
        select.select2({
            placeholder: placeholder
        });

        return this;
    }
});

// Collection of response models
const ResponseCollection = Backbone.Collection.extend({
    model: ResponseModel,

    // Update collection from annotation and study objects
    update: function (responses, questions) {
        let models = _.map(questions, (question) => {
            let questionId = question['id'];
            let model = new ResponseModel({
                id: questionId
            });
            if (responses && _.has(responses, questionId)) {
                let response = responses[questionId];
                model.set('value', response);
            }
            return model;
        });
        this.reset(models);
    }
});

// View for a responses table
const StudyResultsResponsesTableView = View.extend({
    /**
     * @param {ResponseCollection} settings.collection
     */
    initialize: function (settings) {
        this.listenTo(this.collection, 'reset', this.render);
    },

    render: function () {
        this.$el.html(StudyResultsResponsesTableTemplate({
            responses: this.collection.toArray()
        }));

        return this;
    }
});

// View for the annotation results of responses in an annotation
const StudyResultsResponsesView = View.extend({
    /**
     * @param {AnnotationModel} settings.annotation
     * @param {StudyModel} settings.study
     */
    initialize: function (settings) {
        this.annotation = settings.annotation;
        this.study = settings.study;

        this.responses = new ResponseCollection();
        this.listenTo(this.study, 'change', this.render);
        this.listenTo(this.study, 'change', this.updateResponses);
        this.listenTo(this.annotation, 'change', this.updateResponses);

        this.tableView = new StudyResultsResponsesTableView({
            collection: this.responses,
            parentView: this
        });

        this.updateResponses();
        this.render();
    },

    render: function () {
        this.$el.html(StudyResultsResponsesPageTemplate({
            hasQuestions: !_.isEmpty(this.study.get('questions'))
        }));

        this.tableView.setElement(
            this.$('#isic-study-results-responses-table')).render();

        return this;
    },

    updateResponses: function () {
        this.responses.update(
            this.annotation.get('responses'),
            this.study.get('questions')
        );
    }
});

// View for a markup image defined
const StudyResultsMarkupImageView = View.extend({
    /**
     * @param {MarkupImageModel} settings.model
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
        let annotationId = this.model.get('annotationId');
        let markupId = this.model.get('markupId');
        let imageUrl = null;
        if (markupId && annotationId) {
            imageUrl = [
                getApiRoot(),
                'annotation', annotationId,
                'markup', encodeURIComponent(markupId),
                'rendered'
            ].join('/') + '?contentDisposition=inline';
        }

        this.$el.html(StudyResultsMarkupImagePageTemplate({
            imageUrl: imageUrl
        }));

        return this;
    }
});

// View to allow selecting a feature from a study and to display an
// image showing the markup from the annotation
const StudyResultsMarkupsView = View.extend({
    /**
     * @param {AnnotationModel} settings.annotation
     * @param {StudyModel} settings.study
     * @param {MarkupImageModel} settings.markupImageModel
     */
    initialize: function (settings) {
        this.annotation = settings.annotation;
        this.study = settings.study;
        this.markupImageModel = settings.markupImageModel;
        this.markups = new MarkupCollection();

        this.listenTo(this.study, 'change', this.studyChanged);
        this.listenTo(this.annotation, 'change', this.annotationChanged);

        this.selectMarkupView = new StudyResultsSelectMarkupView({
            collection: this.markups,
            parentView: this
        });

        this.listenTo(this.selectMarkupView, 'changed', this.markupChanged);
    },

    studyChanged: function () {
        this.updateMarkupImageModel(null);
        this.render();
    },

    annotationChanged: function () {
        this.markups.update(this.annotation.get('markups'));
        // TODO: pass the old markupId, to prevent it from resetting on every change
        this.updateMarkupImageModel(null);
        this.render();
    },

    markupChanged: function (markupId) {
        this.updateMarkupImageModel(markupId);
    },

    updateMarkupImageModel: function (markupId) {
        this.markupImageModel.set({
            annotationId: this.annotation.id,
            markupId: markupId
        });
    },

    render: function () {
        this.$el.html(StudyResultsMarkupsPageTemplate({
            hasMarkups: !_.isEmpty(this.annotation.get('markups')),
            study: this.study
        }));

        this.selectMarkupView.setElement(
            this.$('#isic-study-results-select-markup-container')).render();

        return this;
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
            this.markupImageView.setVisible(false);
            this.imageView.setVisible(true);
        },

        // Update image visibility when responses tab is activated
        'shown.bs.tab #isic-study-results-responses-tab': function (event) {
            this.imageView.setVisible(false);
            this.markupImageView.setVisible(false);
        },

        // Update image visibility when markups tab is activated
        'shown.bs.tab #isic-study-results-markups-tab': function (event) {
            this.imageView.setVisible(false);
            this.markupImageView.setVisible(true);
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
        this.annotation = new AnnotationModel();
        this.markupImageModel = new MarkupImageModel();

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

        this.responsesView = new StudyResultsResponsesView({
            annotation: this.annotation,
            study: this.study,
            parentView: this
        });

        this.markupsView = new StudyResultsMarkupsView({
            annotation: this.annotation,
            study: this.study,
            markupImageModel: this.markupImageModel,
            parentView: this
        });

        this.imageView = new StudyResultsImageView({
            model: this.image,
            parentView: this
        });

        this.markupImageView = new StudyResultsMarkupImageView({
            model: this.markupImageModel,
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
        this.responsesView.setElement(
            this.$('#isic-study-results-responses-container')).render();
        this.markupsView.setElement(
            this.$('#isic-study-results-markups-container')).render();
        this.imageView.setElement(
            this.$('#isic-study-results-image-preview-container')).render();
        this.markupImageView.setElement(
            this.$('#isic-study-results-markup-image-container')).render();

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
