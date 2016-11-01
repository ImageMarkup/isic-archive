isic.views.TermsOfUseView = isic.View.extend({
    initialize: function () {
        this.render();
    },

    render: function () {
        this.$el.html(isic.templates.termsOfUsePage());

        return this;
    }
});

isic.router.route('terms_of_use', 'termsOfUse', function (id) {
    girder.events.trigger('g:navigateTo', isic.views.TermsOfUseView);
});
