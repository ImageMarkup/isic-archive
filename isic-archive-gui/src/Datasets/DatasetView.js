import LoadingAnimation from '@girder/core/views/widgets/LoadingAnimation';
import AccessWidget from '@girder/core/views/widgets/AccessWidget';

import View from '../view';
import router from '../router';

import DatasetPageTemplate from './datasetPage.pug';
import './datasetPage.styl';
import '../common/Listing/listingItemPage.styl';

const DatasetView = View.extend({
    events: {
        'click .isic-dataset-register-metadata-button': function () {
            router.navigate(
                `dataset/${this.model.id}/metadata/register`,
                {trigger: true});
        },
        'click .isic-dataset-apply-metadata-button': function () {
            router.navigate(
                `dataset/${this.model.id}/metadata/apply`,
                {trigger: true});
        },
        'click .isic-dataset-access-button': function () {
            this.accessWidget = new AccessWidget({
                el: $('#g-dialog-container'),
                model: this.model,
                modelType: 'Dataset',
                hideRecurseOption: true,
                noAccessFlag: true,
                modal: true,
                parentView: this
            });
        }

    },

    /**
     * @param {DatasetModel} settings.model
     */
    initialize: function (settings) {
        // Display loading indicator
        this.loadingAnimation = new LoadingAnimation({
            el: this.el,
            parentView: this
        }).render();

        this.model
            .once('g:fetched', () => {
                // Don't "this.loadingAnimation.destroy()", as it will unbind all events on "this.el"
                delete this.loadingAnimation;

                this.render();
            })
            .fetch();
    },

    render: function () {
        this.$el.html(DatasetPageTemplate({
            dataset: this.model,
            formatDate: this.formatDate
        }));

        return this;
    }
});

export default DatasetView;
