//
// Tasks view
//

// Model for a task
isic.models.TaskModel = girder.Model.extend({
});

// Collection of tasks
isic.collections.TaskCollection = girder.Collection.extend({
    model: isic.models.TaskModel
});

// View for a group of tasks
isic.views.TasksGroupView = isic.View.extend({
    initialize: function (settings) {
        this.title = _.has(settings, 'title') ? settings.title : '';
        this.subtitle = _.has(settings, 'subtitle') ? settings.subtitle : '';
        this.linkPrefix = _.has(settings, 'linkPrefix') ? settings.linkPrefix : '';
        this.resourceName = _.has(settings, 'resourceName') ? settings.resourceName : '';

        this.listenTo(this.collection, 'g:changed', this.render);
    },

    render: function () {
        this.$el.html(isic.templates.taskPage({
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
isic.views.TasksView = isic.View.extend({
    events: {
        'click .isic-tasks-refresh-button': 'fetchTasks'
    },

    initialize: function (settings) {
        if (girder.currentUser.canReviewDataset()) {
            this.reviewTasks = new isic.collections.TaskCollection();
            this.reviewTasks.altUrl = 'task/me/review';
            this.reviewTasks.pageLimit = Number.MAX_SAFE_INTEGER;

            this.taskReviewView = new isic.views.TasksGroupView({
                title: 'Dataset Review',
                subtitle: 'QC review newly uploaded datasets',
                linkPrefix: girder.apiRoot + '/task/me/review/redirect?datasetId=',
                resourceName: 'dataset',
                collection: this.reviewTasks,
                parentView: this
            });
        }

        if (girder.currentUser.getSegmentationSkill() !== null) {
            this.segmentationTasks = new isic.collections.TaskCollection();
            this.segmentationTasks.altUrl = 'task/me/segmentation';
            this.segmentationTasks.pageLimit = Number.MAX_SAFE_INTEGER;

            this.taskSegmentationView = new isic.views.TasksGroupView({
                title: 'Lesion Segmentation',
                subtitle: 'Segment boundaries between lesion and normal skin',
                linkPrefix: girder.apiRoot + '/task/me/segmentation/redirect?datasetId=',
                resourceName: 'dataset',
                collection: this.segmentationTasks,
                parentView: this
            });
        }

        this.annotationTasks = new isic.collections.TaskCollection();
        this.annotationTasks.altUrl = 'task/me/annotation';
        this.annotationTasks.pageLimit = Number.MAX_SAFE_INTEGER;

        this.taskAnnotationView = new isic.views.TasksGroupView({
            title: 'Annotation Studies',
            subtitle: 'Clinical feature annotation studies',
            linkPrefix: girder.apiRoot + '/task/me/annotation/redirect?studyId=',
            resourceName: 'study',
            collection: this.annotationTasks,
            parentView: this
        });

        this.render();

        this.fetchTasks();
    },

    render: function () {
        this.$el.html(isic.templates.tasksPage({
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

isic.router.route('tasks', 'tasks', function () {
    girder.events.trigger('g:navigateTo', isic.views.TasksView);
});
