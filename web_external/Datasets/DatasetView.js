isic.views.DatasetView = isic.View.extend({
    initialize: function (settings) {
        this.dataset = new isic.models.DatasetModel({
            _id: settings.id
        }).once('g:fetched', function () {
            this.render();
        }, this).fetch();
    },

    render: function () {
        this.$el.html(isic.templates.datasetPage({
            dataset: this.dataset,
            formatDate: this.formatDate
        }));

        return this;
    },

    formatDate: function (date) {
        return girder.formatDate(date, girder.DATE_SECOND);
    }
});
