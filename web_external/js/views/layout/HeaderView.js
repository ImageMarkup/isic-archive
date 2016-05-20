isic_archive.views.LayoutHeaderView = isic_archive.View.extend({
    events: {
    },

    render: function () {
        this.$el.html(isic_archive.templates.layoutHeader());

        this.$('a[title]').tooltip({
            placement: 'bottom',
            delay: {show: 300}
        });

        new isic_archive.views.LayoutHeaderUserView({
            el: this.$('.i-current-user-wrapper'),
            parentView: this
        }).render();
    }
});
