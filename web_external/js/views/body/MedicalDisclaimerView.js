isic.views.MedicalDisclaimerView = isic.View.extend({
    initialize: function () {
        this.render();
    },

    render: function () {
        this.$el.html(isic.templates.medicalDisclaimerPage());

        return this;
    }
});

isic.router.route('medicalDisclaimer', 'medicalDisclaimer', function (id) {
    girder.events.trigger('g:navigateTo', isic.views.MedicalDisclaimerView);
});
