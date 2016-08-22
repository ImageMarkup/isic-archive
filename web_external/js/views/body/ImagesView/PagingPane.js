/*globals girder, jQuery, d3, Image*/

isic.views.ImagesSubViews = isic.views.ImagesSubViews || {};

isic.views.ImagesSubViews.PagingPane = Backbone.View.extend({
    initialize: function () {
        var self = this;
        self.listenTo(self.model, 'change:imageIds', self.render);
    },
    render: function () {
        var self = this;
        if (!self.addedImages) {
            // Sneaky hack: the image file name is part of the id; use the id to
            // attach the correct src attribute, as well as the appropriate
            // event listeners
            d3.select(self.el).selectAll('.button')
                .append('img')
                .attr('src', function () {
                    var imgName = this.parentNode.getAttribute('id').slice(12);
                    return girder.staticRoot +
                    '/built/plugins/isic_archive/extra/img/' +
                    imgName + '.svg';
                })
                .on('click', function () {
                    var funcName = this.parentNode.getAttribute('id').slice(12);
                    self[funcName].apply(self, arguments);
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
    },
    seekFirst: function () {
        var self = this;
        self.model.set('offset', 0);
    },
    seekPrev: function () {
        var self = this;
        var page = {
            limit: self.model.get('limit'),
            offset: self.model.get('offset')
        };
        page.offset -= page.limit;
        self.model.set(page);
    },
    seekNext: function () {
        var self = this;
        var page = {
            limit: self.model.get('limit'),
            offset: self.model.get('offset')
        };
        page.offset += page.limit;
        self.model.set(page);
    },
    seekLast: function () {
        var self = this;
        var imageCount = self.model.get('overviewHistogram')
            .__passedFilters__[0].count;
        var limit = self.model.get('limit');
        self.model.set('offset', Math.floor(imageCount / limit) * limit);
    }
});
