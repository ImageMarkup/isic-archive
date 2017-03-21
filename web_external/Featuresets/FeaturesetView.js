isic.views.FeaturesetView = isic.View.extend({
    events: {
        'click .isic-featureset-destroy-button': 'confirmDestroy'
    },

    /**
     * @param {isic.models.FeaturesetModel} settings.model
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
        this.$el.html(isic.templates.featuresetPage({
            featureset: this.model,
            currentUser: girder.currentUser
        }));

        return this;
    },

    confirmDestroy: function () {
        girder.confirm({
            text: '<h4>Permanently delete <b>"' + _.escape(this.model.name()) + '"</b> featureset?</h4>',
            escapedHtml: true,
            confirmCallback: _.bind(function () {
                // Ensure dialog is hidden before continuing. Otherwise,
                // when destroy() displays its modal alert dialog,
                // the Bootstrap-created element with class "modal-backdrop"
                // is erroneously not removed.
                $('#g-dialog-container').on('hidden.bs.modal', _.bind(this.destroy, this));
            }, this)
        });
    },

    destroy: function () {
        this.model.destroy({
            success: function (model, resp, options) {
                isic.showAlertDialog({
                    text: '<h4>Featureset <b>"' + _.escape(model.name()) + '"</b> deleted</h4>',
                    escapedHtml: true
                });
            },
            error: function (model, resp, options) {
                isic.showAlertDialog({
                    text: '<h4>Error deleting featureset</h4><br>' + _.escape(resp.responseJSON.message),
                    escapedHtml: true
                });
            }
        });
    }
});
