isic.views.LayoutHeaderView = isic.View.extend({
    events: {
        'mouseenter .dropdown': function (event) {
            $(event.currentTarget).addClass('open');
        },
        'mouseleave .dropdown': function (event) {
            $(event.currentTarget).removeClass('open');
        },
        'click .dropdown': function (event) {
            $(event.currentTarget).removeClass('open');
        }
    },

    initialize: function (settings) {
        this.render();

        girder.events.on('g:login', this.render, this);
        girder.events.on('g:login-changed', this.render, this);
    },

    render: function () {
        this.$el.html(isic.templates.layoutHeader({
            currentUser: girder.currentUser
        }));

        // Specify trigger for tooltip to ensure that tooltip hides when button
        // is clicked. See http://stackoverflow.com/a/33585981/2522042.
        this.$('a[title]').tooltip({
            placement: 'bottom',
            trigger: 'hover',
            delay: {show: 300}
        });

        new isic.views.LayoutHeaderUserView({
            el: this.$('.isic-current-user-wrapper'),
            parentView: this
        }).render();
    }
});
