// Modal view for dataset license information
isic.views.CreateDatasetLicenseInfoWidget = isic.View.extend({
    render: function () {
        this.$el.html(isic.templates.createDatasetLicenseInfoPage()).girderModal(this);
        return this;
    }
});
