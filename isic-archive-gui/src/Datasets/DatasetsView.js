import $ from 'jquery';

import LoadingAnimation from '@girder/core/views/widgets/LoadingAnimation';
import PaginateWidget from '@girder/core/views/widgets/PaginateWidget';

import DatasetView from './DatasetView';
import DatasetCollection from '../collections/DatasetCollection';
import DatasetModel from '../models/DatasetModel';
import View from '../view';
import router from '../router';

import DatasetsPageTemplate from './datasetsPage.pug';
import './datasetsPage.styl';

const DatasetsView = View.extend({
    // TODO refactor
    events: {
        'show.bs.collapse .isic-listing-panel-collapse': function (event) {
            let target = $(event.target);
            target.parent().find('.icon-right-open').removeClass('icon-right-open').addClass('icon-down-open');

            let viewIndex = parseInt(target.attr('data-model-index'), 10);
            let viewContainer = target.find('.isic-listing-panel-body');
            this.renderDataset(viewIndex, viewContainer);
        },
        'hide.bs.collapse .isic-listing-panel-collapse': function (event) {
            $(event.target).parent().find('.icon-down-open').removeClass('icon-down-open').addClass('icon-right-open');
        },
        'click .isic-dataset-add-button': function () {
            router.navigate('dataset/create', {trigger: true});
        }
    },

    initialize: function (settings) {
        this.loaded = false;

        this.datasets = new DatasetCollection();
        this.listenTo(this.datasets, 'g:changed', () => {
            this.loaded = true;
            this.render();
        });
        this.datasets.fetch();

        this.paginateWidget = new PaginateWidget({
            collection: this.datasets,
            parentView: this
        });

        this.render();
    },

    render: function () {
        this.$el.html(DatasetsPageTemplate({
            title: 'Datasets',
            models: this.datasets,
            loaded: this.loaded,
            canCreateDataset: DatasetModel.canCreate()
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

    renderDataset: function (index, container) {
        if (container.children().length === 0) {
            let dataset = this.datasets.at(index);

            new DatasetView({ // eslint-disable-line no-new
                el: container,
                model: dataset,
                parentView: this
            });
        }
    }
});

export default DatasetsView;
