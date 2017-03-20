isic.views.StudyView = isic.View.extend({
    events: {
        'click .isic-study-add-user-button': function () {
            if (!this.studyAddUserWidget) {
                this.studyAddUserWidget = new isic.views.StudyAddUserWidget({
                    el: $('#g-dialog-container'),
                    study: this.model,
                    parentView: this
                }).on('g:saved', function () {
                    this.model.once('g:fetched', function () {
                        this.render();
                    }, this).fetch();
                }, this);
            }
            this.studyAddUserWidget.render();
        }
    },

    /**
     * @param {isic.models.StudyModel} settings.model
     * @param {boolean} settings.studyAdmin - Whether the current user can admin the study.
     */
    initialize: function (settings) {
        this.studyAdmin = settings.studyAdmin;

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
        this.$el.html(isic.templates.studyPage({
            study: this.model,
            studyAdmin: this.studyAdmin
        }));

        this.$('.isic-tooltip').tooltip({
            delay: 100
        });

        return this;
    }
});
