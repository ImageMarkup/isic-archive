isic.View = girder.View.extend({
    formatDate: function (date) {
        return girder.formatDate(date, girder.DATE_SECOND);
    }
});
