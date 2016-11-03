isic.views.LayoutFooterView = isic.View.extend({
    initialize: function () {
        this.render();
    },

    render: function () {
        this.$el.html(isic.templates.layoutFooter({
            apiRoot: girder.apiRoot
        }));

        this.$('.isic-footer-disclaimer').popover({
            trigger: 'hover',
            placement: 'auto top',
            container: this.$('.isic-footer-links')
        }).click(function () {
            $(this).popover('toggle');
        });

        return this;
    }
});
