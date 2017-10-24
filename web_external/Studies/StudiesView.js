import $ from 'jquery';

import LoadingAnimation from 'girder/views/widgets/LoadingAnimation';
import PaginateWidget from 'girder/views/widgets/PaginateWidget';

import StudyCollection from '../collections/StudyCollection';
import StudyView from './StudyView';
import View from '../view';
import router from '../router';

import StudiesPageTemplate from './studiesPage.pug';
import './studiesPage.styl';

const StudiesView = View.extend({
    // TODO refactor
    events: {
        'show.bs.collapse .isic-listing-panel-collapse': function (event) {
            let target = $(event.target);
            target.parent().find('.icon-right-open').removeClass('icon-right-open').addClass('icon-down-open');

            let viewIndex = parseInt(target.attr('data-model-index'), 10);
            let viewContainer = target.find('.isic-listing-panel-body');
            this.renderStudy(viewIndex, viewContainer);
        },
        'hide.bs.collapse .isic-listing-panel-collapse': function (event) {
            $(event.target).parent().find('.icon-down-open').removeClass('icon-down-open').addClass('icon-right-open');
        },
        'click .isic-study-add-button': function () {
            router.navigate('createStudy', {trigger: true});
        }
    },

    initialize: function (settings) {
        this.loaded = false;
        this.studies = new StudyCollection();

        this.listenTo(this.studies, 'g:changed', () => {
            this.loaded = true;
            this.render();
        });
        this.studies.fetch();

        // TODO: Use the more general 'update' event, once Girder's version of Backbone is upgraded
        this.listenTo(this.studies, 'remove', this.render);

        this.paginateWidget = new PaginateWidget({
            collection: this.studies,
            parentView: this
        });

        this.render();
    },

    render: function () {
        this.$el.html(StudiesPageTemplate({
            title: 'Manage Annotation Studies',
            models: this.studies,
            loaded: this.loaded,
            canCreateStudy: StudyCollection.canCreate()
        }));

        this.paginateWidget.setElement(this.$('.isic-listing-paginate-container')).render();

        // Display loading indicator
        if (!this.loaded) {
            this.loadingAnimation = new LoadingAnimation({
                el: this.$('.isic-listing-loading-animation-container'),
                parentView: this
            }).render();
        } else {
            if (this.loadingAnimation) {
                this.loadingAnimation.destroy();
                delete this.loadingAnimation;
            }
        }

        return this;
    },

    renderStudy: function (index, container) {
        if (container.children().length === 0) {
            let study = this.studies.at(index);

            new StudyView({ // eslint-disable-line no-new
                el: container,
                model: study,
                parentView: this
            });
        }
    }
});

export default StudiesView;
