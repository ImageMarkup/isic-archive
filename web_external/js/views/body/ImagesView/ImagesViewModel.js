/*globals Backbone*/

// This is a pure, backbone-only helper model (i.e. not the same thing
// as the stuff in js/models)

isic.views.ImagesViewModel = Backbone.Model.extend({
    initialize: function () {
        var self = this;
        self.updateCurrentPage();

        // TODO: get more histograms than the overview
        self.updateHistogram('overview');
        // self.updateHistogram('study');
        // self.updateHistogram('filteredSet');
        // self.updateHistogram('page');

        self.listenTo(self, 'change:limit', self.updateCurrentPage);
        self.listenTo(self, 'change:offset', self.updateCurrentPage);
        self.listenTo(self, 'change:filters', self.updateCurrentPage);
        self.listenTo(self, 'change:imageIds', function () {
            self.set('selectedImageId', null);
        });
    },
    events: function () {
        // var _events = {};
        // _events["click " + "#button-" + this.options.count] = "buttonClick";
        // return _events;
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
        girder.restRequest({
            path: 'image/histogram',
            data: requestParams
        }).done(function (resp) {
            self.set(histogramName + 'Histogram', resp);
        });
    },
    updateCurrentPage: function () {
        var self = this;

        // Construct the parameters to send to the server
        var requestParams = {
            limit: self.get('limit'),
            offset: self.get('offset')
        };

        // Validate that the paging settings make sense
        requestParams.limit = Math.max(1, requestParams.limit);
        // Don't allow pages of more than 250 images
        requestParams.limit = Math.min(250, requestParams.limit);

        requestParams.offset = Math.max(0, requestParams.offset);
        // TODO: validate the top range when we have that info from the
        // histogram calculations
        var imageCount = self.get('overviewHistogram').__passedFilters__[0].count;
        console.log('validating:', imageCount, requestParams.limit, requestParams.offset);
        if (requestParams.offset + requestParams.limit > imageCount) {
            requestParams.offset = Math.floor(imageCount / requestParams.limit) *
                requestParams.limit;
        }

        // In case we've overridden anything, update with the cleaned values
        self.set(requestParams, {silent: true});

        // TODO: pass in filter settings
        // var filterString = self.getFilterString();
        girder.restRequest({
            path: 'image',
            data: requestParams
        }).done(function (resp) {
            self.set('imageIds', resp.map(function (imageObj) {
                return imageObj._id;
            }));
        });
    }
});
