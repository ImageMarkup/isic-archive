isic.views.LayoutHeaderView = isic.View.extend({
    events: {
        'click .isic-link-home': function () {
            isic.router.navigate('index', {trigger: true});
        },

        'click .isic-link-dataset-upload': function () {
            isic.router.navigate('uploadDataset', {trigger: true});
        },

        'click .isic-link-studies': function () {
            isic.router.navigate('studies', {trigger: true});
        }
    },

    initialize: function () {
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
        this.$el.html(isic.templates.layoutHeader({
            datasetContributor: this.datasetContributor
        }));

        this.$('a[title]').tooltip({
            placement: 'bottom',
            delay: {show: 300}
        });

        new isic.views.LayoutHeaderUserView({
            el: this.$('.isic-current-user-wrapper'),
            parentView: this
        }).render();
    }
});
