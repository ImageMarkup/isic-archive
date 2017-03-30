isic.views.ImagesPagingPane = Backbone.View.extend({
    events: {
        'click #isic-images-paging-seek-first:not(.disabled)': function () {
            // TODO: cancel any pending fetches before fetching an additional next page; this is
            // best implemented inside ImageCollection.fetch; also ensure that the current page is
            // sync'd with the fetched page, when pages get fetched in rapid sequence
            this.images.fetchFirstPage();
        },
        'click #isic-images-paging-seek-prev:not(.disabled)': function () {
            this.images.fetchPreviousPage();
        },
        'click #isic-images-paging-seek-next:not(.disabled)': function () {
            this.images.fetchNextPage();
        },
        'click #isic-images-paging-seek-last:not(.disabled)': function () {
            this.images.fetchLastPage(this.filteredFacets.total);
        },
        'click #isic-images-paging-downloadZip:not(.disabled)': function () {
            var downloadUrl = girder.apiRoot + '/image/download';
            var filterQuery = JSON.stringify(this.filters.asAst());
            if (filterQuery) {
                downloadUrl += '?filter=' + filterQuery;
            }
            window.location.assign(downloadUrl);
        }
    },
    /**
     * @param {isic.collections.ImagesFacetCollection} settings.completeFacets
     * @param {isic.collections.ImagesFacetCollection} settings.filteredFacets
     * @param {isic.collections.SelectableImageCollection} settings.images
     * @param {isic.collections.ImagesFilters} settings.filters
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
        this.$el.html(isic.templates.imagesPagingPane({
            // TODO: this path should be available in a global
            staticImageRoot: girder.staticRoot + '/built/plugins/isic_archive/extra/img/'
        }));

        this.$('.btn-group>[data-toggle="tooltip"]').tooltip({
            trigger: 'hover',
            container: 'body'
        });
        this.$('[data-toggle="tooltip"]').tooltip({
            trigger: 'hover'
        });

        return this;
    },

    _rerender: function () {
        var hasFilters = this.filteredFacets.total < this.completeFacets.total;
        var hasPaging = this.images.hasPreviousPage() || this.images.hasNextPage();

        // Disable / enable the appropriate paging buttons
        this.$('#isic-images-paging-seek-prev, #isic-images-paging-seek-first')
            .toggleClass('disabled', !this.images.hasPreviousPage());

        this.$('#isic-images-paging-seek-next, #isic-images-paging-seek-last')
            .toggleClass('disabled', !this.images.hasNextPage());

        // Show the relevant explanatory label
        this.$('.isic-images-paging-detailLabel').hide();
        var labelElement;
        if (hasFilters && hasPaging) {
            labelElement = this.$('#isic-images-hasFiltersAndPaging');
        } else if (hasFilters) {
            labelElement = this.$('#isic-images-hasFilters');
        } else if (hasPaging) {
            labelElement = this.$('#isic-images-hasPaging');
        } else {
            labelElement = this.$('#isic-images-noPagingOrFilters');
        }
        labelElement.show();

        // Update the values in the label
        labelElement.find('.isic-images-paging-detailLabel-overview')
          .text(this.completeFacets.total);
        labelElement.find('.isic-images-paging-detailLabel-filteredSet')
          .text(this.filteredFacets.total);
        if (hasPaging) {
            // Use base 1 for the page text labels
            var startImageNum = this.images._currentOffset() + 1;
            var endImageNum = startImageNum + this.images.length - 1;
            labelElement.find('.isic-images-paging-detailLabel-page')
                .text(startImageNum + ' - ' + endImageNum);
        } else {
            labelElement.find('.isic-images-paging-detailLabel-page')
                .text(this.images.length);
        }

        // Move the paging bar
        this.$('#isic-images-paging-bar-pageTotal')
            .css('left', _.bind(function () {
                return (this.images._currentOffset() / this.filteredFacets.total) * 100 + '%';
            }, this))
            .width(_.bind(function () {
                return (this.images.length / this.filteredFacets.total) * 100 + '%';
            }, this));

        this.$('#isic-images-paging-downloadZip').toggleClass(
            'disabled', this.filteredFacets.total === 0);
    }
});
