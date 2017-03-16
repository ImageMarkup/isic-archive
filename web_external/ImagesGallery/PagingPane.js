/*globals d3*/
isic.views.ImagesViewSubViews = isic.views.ImagesViewSubViews || {};

isic.views.ImagesViewSubViews.PagingPane = Backbone.View.extend({
    events: {
        'click #isic-images-seekFirst': 'seekFirst',
        'click #isic-images-seekPrev': 'seekPrev',
        'click #isic-images-seekNext': 'seekNext',
        'click #isic-images-seekLast': 'seekLast',
        'click #isic-images-download-zip:not(.disabled)': function () {
            var downloadUrl = girder.apiRoot + '/image/download';
            var filter = this.model.getFilterAstTree();
            if (filter) {
                downloadUrl += '?filter=' + JSON.stringify(filter);
            }
            window.location.assign(downloadUrl);
        }
    },
    /**
     * @param {isic.views.ImagesViewSubViews.ImagesViewModel} settings.model
     */
    initialize: function (settings) {
        this.listenTo(this.model.images, 'g:changed', this.render);
        this.listenTo(this.model, 'change:filteredSetHistogram', this.render);
        this.listenTo(this.model, 'change:offset', this.updateControls);
        this.listenTo(this.model, 'change:limit', this.updateControls);
    },
    renderBars: function () {
        var pageDetails = this.model.getPageDetails(true);

        // Scale for the bars
        var pageScale = d3.scale.linear()
          .domain([0, pageDetails.filteredSetCount])
          .range([0, this.$('#isic-images-pagingBars').width()]);

        // Now draw the bars indicating the size and location of
        // the page within the current filtered set
        var barData = [
            {
                segment: 'filteredSet',
                offset: 0,
                count: pageDetails.filteredSetCount
            },
            {
                segment: 'page',
                offset: pageDetails.offset,
                count: pageDetails.limit
            }
        ];
        var bars = d3.select(this.el).select('#isic-images-pagingBars')
            .selectAll('div.bar').data(barData, function (d) {
                return d.segment;
            });
        bars.enter().append('div');
        bars.attr('class', function (d) {
            return d.segment + ' bar';
        }).style('left', function (d) {
            return pageScale(d.offset) + 'px';
        }).style('width', function (d) {
            return Math.max(pageScale(d.count + d.offset) -
                pageScale(d.offset), 0) + 'px';
        });
    },
    updateControls: function () {
        var pageDetails = this.model.getPageDetails(true);

        var hasFilters = pageDetails.filteredSetCount < pageDetails.overviewCount;
        var hasPaging = pageDetails.limit < pageDetails.filteredSetCount;

        // Disable / enable the appropriate paging buttons
        if (pageDetails.offset === 0) {
            this.$('#isic-images-seekPrev, #isic-images-seekFirst')
                .addClass('disabled');
        } else {
            this.$('#isic-images-seekPrev, #isic-images-seekFirst')
                .removeClass('disabled');
        }
        if (pageDetails.offset + pageDetails.limit === pageDetails.filteredSetCount) {
            this.$('#isic-images-seekNext, #isic-images-seekLast')
                .addClass('disabled');
        } else {
            this.$('#isic-images-seekNext, #isic-images-seekLast')
                .removeClass('disabled');
        }

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
          .text(pageDetails.overviewCount);
        labelElement.find('span.filteredSet')
          .text(pageDetails.filteredSetCount);
        if (hasPaging) {
            // Use base 1 for the page text labels
            labelElement.find('span.page')
                .text((pageDetails.offset + 1) + ' - ' +
                    (pageDetails.offset + pageDetails.limit));
        } else {
            labelElement.find('span.page')
                .text(pageDetails.filteredSetCount);
        }

        this.$('#isic-images-download-zip').toggleClass(
            'disabled', pageDetails.filteredSetCount === 0);
    },
    render: function () {
        if (!this.addedImages) {
            var imgRoot = girder.staticRoot + '/built/plugins/isic_archive/extra/img/';
            this.$('.button').find('img').each(function (index) {
                var name = $(this).data('name');
                $(this).attr('src', imgRoot + name + '.svg');
            });
            // Set the page size to 50.
            //
            // TODO: offer a pulldown menu with several page size options.
            this.model.set('limit', 50);

            this.addedImages = true;
        }

        this.updateControls();
        this.renderBars();

        this.initializeTooltips();

        return this;
    },
    initializeTooltips: function () {
        this.$('[data-toggle="tooltip"]').tooltip({
            trigger: 'hover'
        });
    },
    seekFirst: function () {
        this.model.set('offset', 0);
    },
    seekPrev: function () {
        var offset = this.model.get('offset');
        this.model.set('offset', offset - this.model.get('limit'));
    },
    seekNext: function () {
        var offset = this.model.get('offset');
        this.model.set('offset', offset + this.model.get('limit'));
    },
    seekLast: function () {
        var details = this.model.getPageDetails(true);
        this.model.set('offset',
            Math.floor(details.filteredSetCount / details.limit) * details.limit);
    }
});
