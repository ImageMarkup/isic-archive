import _ from 'underscore';

import {getCurrentUser} from 'girder/auth';

import Collection from '../collections/Collection';
import Model from '../models/Model';
import View from '../view';

import TasksPageTemplate from './tasksPage.pug';
import './tasksPage.styl';
import TaskPageTemplate from './taskPage.pug';
import './taskPage.styl';

// Model for a task
var TaskModel = Model.extend({
});

// Collection of tasks
var TaskCollection = Collection.extend({
    model: TaskModel
});

// View for a group of tasks
var TasksGroupView = View.extend({
    /**
     * @param {string} settings.title - The title of the task type.
     * @param {string} settings.subtitle - The description of the task type.
     * @param {string} settings.linkPrefix - The URL prefix of the task type.
     * @param {string} settings.resourceName - The property name of the resource, within each task model.
     * @param {TaskCollection} settings.collection
     */
    initialize: function (settings) {
        this.title = _.has(settings, 'title') ? settings.title : '';
        this.subtitle = _.has(settings, 'subtitle') ? settings.subtitle : '';
        this.linkPrefix = _.has(settings, 'linkPrefix') ? settings.linkPrefix : '';
        this.resourceName = _.has(settings, 'resourceName') ? settings.resourceName : '';

        this.listenTo(this.collection, 'g:changed', this.render);
    },

    render: function () {
        this.$el.html(TaskPageTemplate({
            title: this.title,
            subtitle: this.subtitle,
            linkPrefix: this.linkPrefix,
            resourceName: this.resourceName,
            total: this.numTasks(),
            tasks: this.collection.models
        }));

        return this;
    },

    // Return total number of tasks in collection
    numTasks: function () {
        return this.collection.models.reduce(function (total, model) {
            return total + model.get('count');
        }, 0);
    }
});

// View for the task dashboard
var TasksView = View.extend({
    events: {
        'click .isic-tasks-refresh-button': 'fetchTasks'
    },

    initialize: function (settings) {
        var currentUser = getCurrentUser();

        if (currentUser.canReviewDataset()) {
            this.reviewTasks = new TaskCollection();
            this.reviewTasks.altUrl = 'task/me/review';
            this.reviewTasks.pageLimit = Number.MAX_SAFE_INTEGER;

            this.taskReviewView = new TasksGroupView({
                title: 'Dataset Review',
                subtitle: 'QC review newly created datasets',
                linkPrefix: this.apiRoot + '/task/me/review/redirect?datasetId=',
                resourceName: 'dataset',
                collection: this.reviewTasks,
                parentView: this
            });
        }

        if (currentUser.getSegmentationSkill() !== null) {
            this.segmentationTasks = new TaskCollection();
            this.segmentationTasks.altUrl = 'task/me/segmentation';
            this.segmentationTasks.pageLimit = Number.MAX_SAFE_INTEGER;

            this.taskSegmentationView = new TasksGroupView({
                title: 'Lesion Segmentation',
                subtitle: 'Segment boundaries between lesion and normal skin',
                linkPrefix: this.apiRoot + '/task/me/segmentation/redirect?datasetId=',
                resourceName: 'dataset',
                collection: this.segmentationTasks,
                parentView: this
            });
        }

        this.annotationTasks = new TaskCollection();
        this.annotationTasks.altUrl = 'task/me/annotation';
        this.annotationTasks.pageLimit = Number.MAX_SAFE_INTEGER;

        this.taskAnnotationView = new TasksGroupView({
            title: 'Annotation Studies',
            subtitle: 'Clinical feature annotation studies',
            linkPrefix: this.apiRoot + '/task/me/annotation/redirect?studyId=',
            resourceName: 'study',
            collection: this.annotationTasks,
            parentView: this
        });

        this.render();

        this.fetchTasks();
    },

    render: function () {
        this.$el.html(TasksPageTemplate({
            title: 'Task Dashboard'
        }));

        if (this.taskReviewView) {
            this.taskReviewView.setElement(
                this.$('#isic-tasks-qc-container')).render();
        }
        if (this.taskSegmentationView) {
            this.taskSegmentationView.setElement(
                this.$('#isic-tasks-segmentation-container')).render();
        }
        this.taskAnnotationView.setElement(
            this.$('#isic-tasks-annotation-container')).render();

        this.$('.isic-tooltip').tooltip({
            delay: 100
        });

        return this;
    },

    fetchTasks: function () {
        if (this.reviewTasks) {
            this.reviewTasks.fetch();
        }
        if (this.segmentationTasks) {
            this.segmentationTasks.fetch({
                details: false
            });
        }
        this.annotationTasks.fetch();
    }
});

export default TasksView;
