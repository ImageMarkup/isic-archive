isic.views.StudyView = isic.View.extend({
    events: {
        'click .isic-study-add-user-button': function () {
            if (!this.studyAddUserWidget) {
                this.studyAddUserWidget = new isic.views.StudyAddUserWidget({
                    el: $('#g-dialog-container'),
                    study: this.study,
                    parentView: this
                }).on('g:saved', function () {
                    this.study.once('g:fetched', function () {
                        this.render();
                    }, this).fetch();
                }, this);
            }
            this.studyAddUserWidget.render();
        }
    },

    initialize: function (settings) {
        this.studyAdmin = settings.studyAdmin;

        this.study = new isic.models.StudyModel({
            _id: settings.id
        }).once('g:fetched', function () {
            this.render();
        }, this).fetch();
    },

    render: function () {
        this.$el.html(isic.templates.studyPage({
            study: this.study,
            studyAdmin: this.studyAdmin
        }));

        this.$('.isic-tooltip').tooltip({
            delay: 100
        });

        return this;
    }
});
