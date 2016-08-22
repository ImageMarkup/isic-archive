/*globals Backbone*/

// This is a pure, backbone-only helper model (i.e. not the same thing
// as the stuff in js/models)

isic.views.ImagesViewModel = Backbone.Model.extend({
    initialize: function () {
        var self = this;
        self.updateCurrentPage();

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
        histograms: {
            __passedFilters__: [{
                count: 0,
                label: 'count'
            }]
        }
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
        /*
        var imageCount = self.get('histograms').__passedFilters__[0].count;
        if (requestParams.offset + requestParams.limit > imageCount) {
            offset = Math.floor(imageCount / requestParams.limit) *
                requestParams.limit;
        }
        */

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
