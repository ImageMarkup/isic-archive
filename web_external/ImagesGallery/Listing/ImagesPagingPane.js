import 'bootstrap/js/dropdown';

import {getApiRoot} from 'girder/rest';

import View from '../../view';

import ImagesPagingPaneTemplate from './imagesPagingPane.pug';
import './imagesPagingPane.styl';

const ImagesPagingPane = View.extend({
    events: {
        'click #isic-images-paging-seek-first': function () {
            // TODO: cancel any pending fetches before fetching an additional next page; this is
            // best implemented inside ImageCollection.fetch; also ensure that the current page is
            // sync'd with the fetched page, when pages get fetched in rapid sequence
            this.images.fetchFirstPage();
        },
        'click #isic-images-paging-seek-prev': function () {
            this.images.fetchPreviousPage();
        },
        'click #isic-images-paging-seek-next': function () {
            this.images.fetchNextPage();
        },
        'click #isic-images-paging-seek-last': function () {
            this.images.fetchLastPage(this.filteredFacets.total);
        },
        'click #isic-images-paging-downloadZip-all': function () {
            this._downloadZip('all');
        },
        'click #isic-images-paging-downloadZip-images': function () {
            this._downloadZip('images');
        },
        'click #isic-images-paging-downloadZip-metadata': function () {
            this._downloadZip('metadata');
        }
    },

    /**
     * @param {ImagesFacetCollection} settings.completeFacets
     * @param {ImagesFacetCollection} settings.filteredFacets
     * @param {SelectableImageCollection} settings.images
     * @param {ImagesFilter} settings.filters
     */
    initialize: function (settings) {
        this.completeFacets = settings.completeFacets;
        this.filteredFacets = settings.filteredFacets;
        this.images = settings.images;
        this.filters = settings.filters;

        // TODO: Use the more general 'update' event, once Girder's version of Backbone is upgraded
        this.listenTo(this.images, 'g:changed', this._rerender);
        this.listenTo(this.filteredFacets, 'sync', this._rerender);

        // TODO: disable controls (things in updateControls) on any of
        // this.completeFacets, this.filteredFacets, this.images fetch,
        // to prevent multiple interactions

        this.render();
    },

    render: function () {
        this.$el.html(ImagesPagingPaneTemplate());

        return this;
    },

    _rerender: function () {
        let hasFilters = this.filteredFacets.total < this.completeFacets.total;
        let hasPaging = this.images.hasPreviousPage() || this.images.hasNextPage();

        // Disable / enable the appropriate paging buttons
        this.$('#isic-images-paging-seek-prev, #isic-images-paging-seek-first')
            .girderEnable(this.images.hasPreviousPage());
        this.$('#isic-images-paging-seek-next, #isic-images-paging-seek-last')
            .girderEnable(this.images.hasNextPage());

        // Show the relevant explanatory label
        this.$('#isic-images-paging-label>*').hide();
        let labelElement;
        if (hasFilters && hasPaging) {
            labelElement = this.$('#isic-images-paging-label-hasFiltersAndPaging');
        } else if (hasFilters) {
            labelElement = this.$('#isic-images-paging-label-hasFilters');
        } else if (hasPaging) {
            labelElement = this.$('#isic-images-paging-label-hasPaging');
        } else {
            labelElement = this.$('#isic-images-paging-label-noPagingOrFilters');
        }
        labelElement.show();

        // Update the values in the label
        labelElement.find('.isic-images-paging-label-total')
            .text(this.completeFacets.total);
        labelElement.find('.isic-images-paging-label-filtered')
            .text(this.filteredFacets.total);
        if (hasPaging) {
            // Use base 1 for the page text labels
            let startImageNum = this.images._currentOffset() + 1;
            let endImageNum = startImageNum + this.images.length - 1;
            labelElement.find('.isic-images-paging-label-page')
                .text(`${startImageNum} - ${endImageNum}`);
        } else {
            labelElement.find('.isic-images-paging-label-page')
                .text(this.images.length);
        }

        // Move the paging bar
        this.$('#isic-images-paging-bar-pageTotal')
            .css('left', () => `${(this.images._currentOffset() / this.filteredFacets.total) * 100}%`)
            .width(() => `${(this.images.length / this.filteredFacets.total) * 100}%`);

        this.$('#isic-images-paging-downloadZip>button').girderEnable(this.filteredFacets.total > 0);
    },

    _downloadZip: function (include) {
        let downloadUrl = `${getApiRoot()}/image/download?include=${include}`;
        let filterQuery = JSON.stringify(this.filters.asAst());
        if (filterQuery) {
            downloadUrl += `&filter=${filterQuery}`;
        }
        window.location.assign(downloadUrl);
    }
});

export default ImagesPagingPane;
