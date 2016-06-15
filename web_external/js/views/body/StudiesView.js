isic.views.StudiesView = isic.View.extend({
    events: {
        'show.bs.collapse .isic-study-panel-collapse': function (event) {
            var target = $(event.target);
            target.parent().find('.icon-right-open').removeClass('icon-right-open').addClass('icon-down-open');

            var viewIndex = window.parseInt(target.attr('data-study-index'), 10);
            var viewContainer = target.find('.isic-study-panel-body');
            this.renderStudy(viewIndex, viewContainer);
        },
        'hide.bs.collapse .isic-study-panel-collapse': function (event) {
            $(event.target).parent().find('.icon-down-open').removeClass('icon-down-open').addClass('icon-right-open');
        }
    },

    initialize: function (settings) {
        // TODO: filter by state?
        this.studies = new isic.collections.StudyCollection();
        this.studies.once('g:changed', function () {
            this.render();
        }, this).fetch();

        this.render();
    },

    render: function () {
        this.$el.html(isic.templates.studiesPage({
            studies: this.studies
        }));

        return this;
    },

    renderStudy: function (index, container) {
        if (container.children().length === 0) {
            var studyId = this.studies.at(index).id;

            // Display loading indicator
            new girder.views.LoadingAnimation({
                el: container,
                parentView: this
            }).render();

            new isic.views.StudyView({ // eslint-disable-line no-new
                el: container,
                id: studyId,
                parentView: this
            });
        }
    }
});

isic.router.route('studies', 'studies', function (id) {
    girder.events.trigger('g:navigateTo', isic.views.StudiesView);
});
