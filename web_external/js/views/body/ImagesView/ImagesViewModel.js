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
        histogram: {}
    },
    updateCurrentPage: function () {
        var self = this;
        // TODO: pass in filter settings
        // var filterString = self.getFilterString();
        girder.restRequest({
            path: 'image',
            data: {
                'limit': self.get('limit'),
                'offset': self.get('offset')
            }
        }).done(function (resp) {
            self.set('imageIds', resp.map(function (imageObj) {
                return imageObj._id;
            }));
        });
    }
});
