isic.views.StudyView = isic.View.extend({
    initialize: function (settings) {
        girder.cancelRestRequests('fetch');

        if (settings.study) {
            this.study = settings.study;
            this.render();
        } else if (settings.id) {
            this.study = new isic.models.StudyModel({
                _id: settings.id
            }).once('g:fetched', function () {
                this.render();
            }, this).fetch();
        } else {
            // TODO: usage error
        }
    },

    render: function () {
        this.$el.html(isic.templates.studyPage({
            study: this.study
        }));

        return this;
    }
});
