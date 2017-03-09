isic.views.TermsAcceptanceView = isic.View.extend({
    events: {
        'click #isic-terms-accept': function (event) {
            // Disable buttons while request is pending
            var buttons = this.$('.isic-terms-agreement-button-container button');
            buttons.prop('disabled', true);

            isic.models.UserModel.currentUserSetAcceptTerms(function () {
                // Refresh page
                Backbone.history.loadUrl();
            });
        },
        'click #isic-terms-reject': function (event) {
            // Route to home page
            isic.router.navigate('', {trigger: true});
        }
    },

    initialize: function (settings) {
        this.termsOfUseWidget = new isic.views.TermsOfUseWidget({
            parentView: this
        });

        this.render();
    },

    render: function () {
        this.$el.html(isic.templates.termsAcceptancePage());

        this.termsOfUseWidget.setElement(
            this.$('#isic-terms-of-use-container')).render();

        return this;
    }
});

isic.router.route('termsAcceptance', 'termsAcceptance', function () {
    girder.events.trigger('g:navigateTo', isic.views.TermsAcceptanceView);
});
