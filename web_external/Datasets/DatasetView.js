isic.views.DatasetView = isic.View.extend({
    events: {
        'click .isic-dataset-register-metadata-button': function () {
            isic.router.navigate('uploadDatasetMetadata/' + this.dataset.id, {trigger: true});
        }
    },

    initialize: function (settings) {
        this.dataset = new isic.models.DatasetModel({
            _id: settings.id
        }).once('g:fetched', function () {
            this.render();
        }, this).fetch();
    },

    render: function () {
        this.$el.html(isic.templates.datasetPage({
            user: girder.currentUser,
            dataset: this.dataset,
            formatDate: this.formatDate
        }));

        return this;
    },

    formatDate: function (date) {
        return girder.formatDate(date, girder.DATE_SECOND);
    }
});
