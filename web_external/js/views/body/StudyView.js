isic.views.StudyView = isic.View.extend({
    initialize: function (settings) {
        this.study = new isic.models.StudyModel({
            _id: settings.id
        }).once('g:fetched', function () {
            this.render();
        }, this).fetch();
    },

    render: function () {
        this.$el.html(isic.templates.studyPage({
            study: this.study
        }));

        return this;
    }
});
