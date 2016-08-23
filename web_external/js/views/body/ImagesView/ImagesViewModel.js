/*globals Backbone*/

// This is a pure, backbone-only helper model (i.e. not the same thing
// as the stuff in js/models)

isic.views.ImagesViewModel = Backbone.Model.extend({
    initialize: function () {
        var self = this;

        self.updateHistogram('overview');
        self.updateHistogram('filteredSet').then(function () {
            return self.updateCurrentPage();
        }).then(function () {
            return self.updateHistogram('page');
        });

        self.listenTo(self, 'change:limit', self.updateCurrentPage);
        self.listenTo(self, 'change:offset', self.updateCurrentPage);
        self.listenTo(self, 'change:filters', self.updateCurrentPage);
        self.listenTo(self, 'change:imageIds', function () {
            self.set('selectedImageId', null);
        });
    },
    defaults: {
        limit: 50,
        offset: 0,
        selectedImageId: null,
        filters: [],
        imageIds: [],
        overviewHistogram: {
            __passedFilters__: [{
                count: 0,
                label: 'count'
            }]
        },
        studyHistogram: {
            __passedFilters__: [{
                count: 0,
                label: 'count'
            }]
        },
        filteredSetHistogram: {
            __passedFilters__: [{
                count: 0,
                label: 'count'
            }]
        },
        pageHistogram: {
            __passedFilters__: [{
                count: 0,
                label: 'count'
            }]
        }
    },
    updateHistogram: function (histogramName) {
        var self = this;
        var requestParams = {};

        /*
        TODO: send parameters, depending on which type of histogram that we want
        if (histogramName === 'page') {
            requestParams.limit = self.get('limit');
            requestParams.offset = self.get('offset');
        }
        if (histogramName === 'page' || histogramName === 'filteredSet') {
            requestParams.filters = self.getFilterString();
        }
        */
        return girder.restRequest({
            path: 'image/histogram',
            data: requestParams
        }).then(function (resp) {
            self.set(histogramName + 'Histogram', resp);
        });
    },
    updateCurrentPage: function () {
        var self = this;

        // Construct the parameters to send to the server
        var requestParams = self.getPageDetails(true);

        // First cap the page size by how many images are available
        requestParams.limit = Math.min(requestParams.filteredSetCount,
            requestParams.limit);
        // The page must include at least one image
        requestParams.limit = Math.max(1, requestParams.limit);
        // Don't allow pages of more than 250 images
        requestParams.limit = Math.min(250, requestParams.limit);

        // Can't have a negative offset
        requestParams.offset = Math.max(0, requestParams.offset);
        // Limit the last page by how many images are available
        if (requestParams.offset + requestParams.limit >
                requestParams.filteredSetCount) {
            requestParams.offset = Math.floor(
                requestParams.filteredSetCount / requestParams.limit) *
                requestParams.limit;
        }

        // In case we've overridden anything, update with the cleaned values
        self.set(requestParams, {silent: true});

        // TODO: pass in filter settings
        // var filterString = self.getFilterString();
        return girder.restRequest({
            path: 'image',
            data: requestParams
        }).then(function (resp) {
            self.set('imageIds', resp.map(function (imageObj) {
                return imageObj._id;
            }));
        });
    },
    getPageDetails: function (skipLimitCap) {
        var self = this;
        var result = {
            overviewCount: self.get('overviewHistogram').__passedFilters__[0].count,
            filteredSetCount: self.get('filteredSetHistogram').__passedFilters__[0].count,
            offset: self.get('offset'),
            limit: self.get('limit')
        };
        if (!skipLimitCap &&
                result.offset + result.limit > result.filteredSetCount) {
            result.limit = result.filteredSetCount - result.offset;
        }
        return result;
    }
});
