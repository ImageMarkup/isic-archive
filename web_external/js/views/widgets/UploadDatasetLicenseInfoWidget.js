// Modal view for dataset license information
isic.views.UploadDatasetLicenseInfoWidget = isic.View.extend({
    render: function () {
        this.$el.html(isic.templates.uploadDatasetLicenseInfoPage()).girderModal(this);
        return this;
    }
});
