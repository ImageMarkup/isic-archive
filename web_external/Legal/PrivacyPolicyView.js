isic.views.PrivacyPolicyView = isic.View.extend({
    initialize: function () {
        this.render();
    },

    render: function () {
        this.$el.html(isic.templates.privacyPolicyPage());

        return this;
    }
});

isic.router.route('privacyPolicy', 'privacyPolicy', function (id) {
    girder.events.trigger('g:navigateTo', isic.views.PrivacyPolicyView);
});
