isic.views.LayoutHeaderView = isic.View.extend({
    events: {
        'click .isic-link-home': function () {
            isic.router.navigate('index', {trigger: true});
        },

        'click .isic-link-forum': function () {
            isic.router.navigate('forum', {trigger: true});
        },

        'click .isic-link-dataset-upload': function () {
            isic.router.navigate('uploadDataset', {trigger: true});
        },

        'click .isic-link-images': function () {
            isic.router.navigate('images', {trigger: true});
        },

        'click .isic-link-studies': function () {
            isic.router.navigate('studies', {trigger: true});
        },

        'click .isic-link-featuresets': function () {
            isic.router.navigate('featuresets', {trigger: true});
        },

        'click .isic-link-tasks': function () {
            isic.router.navigate('tasks', {trigger: true});
        }
    },

    initialize: function () {
        this.datasetContributor = false;

        this._updateUserInfo();

        girder.events.on('g:login', this._updateUserInfo, this);

        this.render();
    },

    render: function () {
        this.$el.html(isic.templates.layoutHeader({
            datasetContributor: this.datasetContributor
        }));

        // Specify trigger for tooltip to ensure that tooltip hides when button
        // is clicked. See http://stackoverflow.com/a/33585981/2522042.
        this.$('a[title]').tooltip({
            placement: 'bottom',
            trigger: 'hover',
            delay: {show: 300}
        });

        new isic.views.LayoutHeaderUserView({
            el: this.$('.isic-current-user-wrapper'),
            parentView: this
        }).render();
    },

    _updateUserInfo: function () {
        // Check whether user has permission to contribute datasets
        var datasetModel = new isic.models.DatasetModel();
        datasetModel.userCanContribute(girder.currentUser).then(_.bind(function (datasetContributor) {
            if (this.datasetContributor !== datasetContributor) {
                this.datasetContributor = datasetContributor;
                this.render();
            }
        }, this));
    }
});
