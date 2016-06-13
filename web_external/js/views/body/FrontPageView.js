isic.views.FrontPageView = girder.views.FrontPageView.extend({
    events: {
        'click .isic-studies-button': function () {
            isic.router.navigate('studies', {trigger: true});
        },

        'click .isic-upload-dataset-button': function () {
            isic.router.navigate('uploadDataset', {trigger: true});
        }
    },

    initialize: function () {
        girder.cancelRestRequests('fetch');

        this.datasetContributor = false;

        // Check whether user has permission to contribute datasets
        var datasetModel = new isic.models.DatasetModel();
        datasetModel.userCanContribute(girder.currentUser, _.bind(function (datasetContributor) {
            this.datasetContributor = datasetContributor;
            this.render();
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
