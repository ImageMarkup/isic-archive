isic.views.DatasetView = isic.View.extend({
    events: {
        'click .isic-dataset-register-metadata-button': function () {
            isic.router.navigate(
                'dataset/' + this.model.id + '/metadata/register',
                {trigger: true});
        },
        'click .isic-dataset-apply-metadata-button': function () {
            isic.router.navigate(
                'dataset/' + this.model.id + '/metadata/apply',
                {trigger: true});
        }
    },

    /**
     * @param {isic.models.DatasetModel} settings.model
     */
    initialize: function (settings) {
        // Display loading indicator
        this.loadingAnimation = new girder.views.LoadingAnimation({
            el: this.el,
            parentView: this
        }).render();

        this.model.once('g:fetched', function () {
            // Don't "this.loadingAnimation.destroy()", as it will unbind all events on "this.el"
            delete this.loadingAnimation;

            this.render();
        }, this).fetch();
    },

    render: function () {
        this.$el.html(isic.templates.datasetPage({
            currentUser: girder.currentUser,
            dataset: this.model,
            formatDate: this.formatDate
        }));

        return this;
    },

    formatDate: function (date) {
        return girder.formatDate(date, girder.DATE_SECOND);
    }
});
