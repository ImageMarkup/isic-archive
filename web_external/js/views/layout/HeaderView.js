isic.views.LayoutHeaderView = isic.View.extend({
    events: {
    },

    render: function () {
        this.$el.html(isic.templates.layoutHeader());

        this.$('a[title]').tooltip({
            placement: 'bottom',
            delay: {show: 300}
        });

        new isic.views.LayoutHeaderUserView({
            el: this.$('.isic-current-user-wrapper'),
            parentView: this
        }).render();
    }
});
