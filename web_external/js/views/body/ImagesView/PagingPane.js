/*globals girder, jQuery, d3, Image*/

isic.views.ImagesViewSubViews = isic.views.ImagesViewSubViews || {};

isic.views.ImagesViewSubViews.PagingPane = Backbone.View.extend({
    initialize: function () {
        var self = this;
        self.listenTo(self.model, 'change:imageIds', self.render);
        self.listenTo(self.model, 'change:overviewHistogram', self.renderBars);
        self.listenTo(self.model, 'change:offset', self.updateControls);
        self.listenTo(self.model, 'change:limit', self.updateControls);
    },
    renderBars: function () {
        var self = this;
        var pageDetails = self.model.getPageDetails();

        // Scale for the bars
        var pageScale = d3.scale.linear()
          .domain([0, pageDetails.filteredSetCount])
          .range([0, self.$el.find('#isic-images-pagingBars').width()]);

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
        var self = this;
        var pageDetails = self.model.getPageDetails();

        var hasFilters = pageDetails.filteredSetCount < pageDetails.overviewCount;
        var hasPaging = pageDetails.limit < pageDetails.filteredSetCount;

        // Disable / enable the appropriate paging buttons
        if (pageDetails.offset === 0) {
            this.$el.find('#isic-images-seekPrev, #isic-images-seekFirst')
                .addClass('disabled');
        } else {
            this.$el.find('#isic-images-seekPrev, #isic-images-seekFirst')
                .removeClass('disabled');
        }
        if (pageDetails.offset + pageDetails.limit === pageDetails.filteredSetCount) {
            this.$el.find('#isic-images-seekNext, #isic-images-seekLast')
                .addClass('disabled');
        } else {
            this.$el.find('#isic-images-seekNext, #isic-images-seekLast')
                .removeClass('disabled');
        }

        // Show the relevant explanatory label
        this.$el.find('.detailLabel').hide();
        var labelElement;
        if (hasFilters && hasPaging) {
            labelElement = this.$el.find('#isic-images-hasFiltersAndPaging');
        } else if (hasFilters) {
            labelElement = this.$el.find('#isic-images-hasFilters');
        } else if (hasPaging) {
            labelElement = this.$el.find('#isic-images-hasPaging');
        } else {
            labelElement = this.$el.find('#isic-images-noPagingOrFilters');
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
    },
    render: function () {
        var self = this;
        if (!self.addedImages) {
            // Sneaky hack: the image file name is part of the id; use the id to
            // attach the correct src attribute, as well as the appropriate
            // event listeners
            d3.select(self.el).selectAll('.button')
                .on('click', function () {
                    var funcName = this.getAttribute('id').slice(12);
                    self[funcName].apply(self, arguments);
                })
                .append('img')
                .attr('src', function () {
                    var imgName = this.parentNode.getAttribute('id').slice(12);
                    return girder.staticRoot +
                    '/built/plugins/isic_archive/extra/img/' +
                    imgName + '.svg';
                });
            // Listen for page size adjustments
            self.$el.find('#isic-images-pageSize').on('change', function () {
                self.model.set('limit', this.value);
                // Invalid values will be capped; update the field if that happens
                var newLimit = self.model.get('limit');
                if (newLimit !== this.value) {
                    this.value = newLimit;
                }
            });
            self.addedImages = true;
        }

        self.updateControls();
        self.renderBars();

        return this;
    },
    seekFirst: function () {
        var self = this;
        self.model.set('offset', 0);
    },
    seekPrev: function () {
        var self = this;
        var offset = self.model.get('offset');
        self.model.set('offset', offset - self.model.get('limit'));
    },
    seekNext: function () {
        var self = this;
        var offset = self.model.get('offset');
        self.model.set('offset', offset + self.model.get('limit'));
    },
    seekLast: function () {
        var self = this;
        var details = self.model.getPageDetails();
        self.model.set('offset',
            Math.floor(details.filteredSetCount / details.limit) * details.limit);
    }
});
