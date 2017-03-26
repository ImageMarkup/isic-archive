isic.views.ImagesPagingPane = Backbone.View.extend({
    events: {
        'click #isic-images-seekFirst:not(.disabled)': function () {
            this.images.fetchFirstPage();
        },
        'click #isic-images-seekPrev:not(.disabled)': function () {
            this.images.fetchPreviousPage();
        },
        'click #isic-images-seekNext:not(.disabled)': function () {
            this.images.fetchNextPage();
        },
        'click #isic-images-seekLast:not(.disabled)': function () {
            this.images.fetchLastPage(this.filteredFacets.total);
        },
        'click #isic-images-download-zip:not(.disabled)': function () {
            var filterQuery = JSON.stringify(this.filters.asAst());
            window.location.assign(girder.apiRoot + '/image/download?filter=' + filterQuery);
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

        this.$('[data-toggle="tooltip"]').tooltip({
            trigger: 'hover'
        });

        return this;
    },

    _rerender: function () {
        var hasFilters = this.filteredFacets.total < this.completeFacets.total;
        var hasPaging = this.images.hasPreviousPage() || this.images.hasNextPage();

        // Disable / enable the appropriate paging buttons
        this.$('#isic-images-seekPrev, #isic-images-seekFirst')
            .toggleClass('disabled', !this.images.hasPreviousPage());

        this.$('#isic-images-seekNext, #isic-images-seekLast')
            .toggleClass('disabled', !this.images.hasNextPage());

        // Show the relevant explanatory label
        this.$('.detailLabel').hide();
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
        labelElement.find('span.overview')
          .text(this.completeFacets.total);
        labelElement.find('span.filteredSet')
          .text(this.filteredFacets.total);
        if (hasPaging) {
            // Use base 1 for the page text labels
            var startImageNum = this.images._currentOffset() + 1;
            var endImageNum = startImageNum + this.images.length - 1;
            labelElement.find('span.page')
                .text(startImageNum + ' - ' + endImageNum);
        } else {
            labelElement.find('span.page')
                .text(this.images.length);
        }

        // Move the paging bar
        this.$('#isic-images-pagingBars .page')
            .css('left', _.bind(function () {
                return (this.images._currentOffset() / this.filteredFacets.total) * 100 + '%';
            }, this))
            .width(_.bind(function () {
                return (this.images.length / this.filteredFacets.total) * 100 + '%';
            }, this));

        this.$('#isic-images-download-zip').toggleClass(
            'disabled', this.filteredFacets.total === 0);
    }
});
