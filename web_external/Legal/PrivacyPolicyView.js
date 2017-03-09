isic.views.PrivacyPolicyView = isic.View.extend({
    initialize: function (settings) {
        this.render();
    },

    render: function () {
        this.$el.html(isic.templates.privacyPolicyPage());

        return this;
    }
});

isic.router.route('privacyPolicy', 'privacyPolicy', function () {
    girder.events.trigger('g:navigateTo', isic.views.PrivacyPolicyView);
});
