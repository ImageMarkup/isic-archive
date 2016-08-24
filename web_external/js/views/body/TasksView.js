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
    initialize: function (settings) {
        this.qcTasks = new isic.collections.TaskCollection();
        this.qcTasks.altUrl = 'uda/task/qc';
        this.qcTasks.pageLimit = Number.MAX_SAFE_INTEGER;

        this.segmentationTasks = new isic.collections.TaskCollection();
        this.segmentationTasks.altUrl = 'task/me/segmentation';
        this.segmentationTasks.pageLimit = Number.MAX_SAFE_INTEGER;

        this.annotationTasks = new isic.collections.TaskCollection();
        this.annotationTasks.altUrl = 'task/me/annotation';
        this.annotationTasks.pageLimit = Number.MAX_SAFE_INTEGER;

        this.taskQCView = new isic.views.TasksGroupView({
            title: 'Phase 0',
            subtitle: 'Images to QC',
            linkPrefix: '/uda/task/p0/',
            resourceName: 'dataset',
            collection: this.qcTasks,
            parentView: this
        });

        this.taskSegmentationView = new isic.views.TasksGroupView({
            title: 'Lesion Segmentation',
            subtitle: 'Segment boundaries between lesion and normal skin',
            linkPrefix: girder.apiRoot + '/task/me/segmentation/redirect?datasetId=',
            resourceName: 'dataset',
            collection: this.segmentationTasks,
            parentView: this
        });

        this.taskAnnotationView = new isic.views.TasksGroupView({
            title: 'Annotation Studies',
            subtitle: 'Clinical feature annotation studies',
            linkPrefix: girder.apiRoot + '/task/me/annotation/redirect?studyId=',
            resourceName: 'study',
            collection: this.annotationTasks,
            parentView: this
        });

        this.render();

        this.qcTasks.fetch();
        this.segmentationTasks.fetch();
        this.annotationTasks.fetch();
    },

    render: function () {
        this.$el.html(isic.templates.tasksPage({
            title: 'Task Dashboard'
        }));

        this.taskQCView.setElement(
            this.$('#isic-tasks-qc-container')).render();
        this.taskSegmentationView.setElement(
            this.$('#isic-tasks-segmentation-container')).render();
        this.taskAnnotationView.setElement(
            this.$('#isic-tasks-annotation-container')).render();

        return this;
    }
});

isic.router.route('tasks', 'tasks', function (id) {
    girder.events.trigger('g:navigateTo', isic.views.TasksView);
});
