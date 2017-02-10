isic.views.TermsOfUseWidget = isic.View.extend({
    render: function () {
        this.$el.html(isic.templates.termsOfUseWidget({
            documentsRoot: girder.staticRoot + '/built/plugins/isic_archive/extra/documents'
        }));
    }
});
