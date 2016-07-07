isic.views.FrontPageView = girder.views.FrontPageView.extend({
    events: {
        'click .isic-button-studies': function () {
            isic.router.navigate('studies', {trigger: true});
        },

        'click .isic-button-dataset-upload': function () {
            isic.router.navigate('uploadDataset', {trigger: true});
        }
    },

    initialize: function () {
        this.datasetContributor = false;

        // Check whether user has permission to contribute datasets.
        //
        // This view is recreated if user logs in/out, so there's no need to
        // observe the 'g:login' event.
        var datasetModel = new isic.models.DatasetModel();
        datasetModel.userCanContribute(girder.currentUser).then(_.bind(function (datasetContributor) {
            if (this.datasetContributor !== datasetContributor) {
                this.datasetContributor = datasetContributor;
                this.render();
            }
        }, this));

        this.render();
    },

    render: function () {
        this.$el.addClass('isic-body-nopad');

        this.$el.html(isic.templates.frontPage({
            apiRoot: girder.apiRoot,
            staticRoot: girder.staticRoot,
            datasetContributor: this.datasetContributor,
            versionInfo: girder.versionInfo
        }));

        return this;
    }
});

isic.router.route('', 'index', function () {
    girder.events.trigger('g:navigateTo', isic.views.FrontPageView);
});
