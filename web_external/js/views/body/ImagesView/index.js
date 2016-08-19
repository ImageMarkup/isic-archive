/*globals girder, jQuery, d3, Image*/
/*eslint-disable*/

isic.views.ImagesSubViews = isic.views.ImagesSubViews || {};

isic.views.ImagesView = isic.View.extend({
  initialize: function () {
    var self = this;
    // Initialize our subviews
    self.histogramPane = new isic.views.ImagesSubViews.HistogramPane();
    self.imageWall = new isic.views.ImagesSubViews.ImageWall();

    self.listenTo(self.histogramPane, 'imagesView:changedFilters',
      function () {
        self.updateCurrentPage();
      });

    window.onresize = function () {
      self.render();
    };
    self.updateCurrentPage();
  },
  updateCurrentPage: function () {
    var self = this;
    // TODO: pass in filters and paging settings
    // var filterString = self.histogramPane.getFilterString();
    girder.restRequest({
      path: 'image',
      data: {
        'limit': 50,
        'offset': 0
      }
    }).done(function (resp) {
      var newImageIds = resp.map(function (imageObj) {
        return imageObj._id;
      });
      self.imageWall.setImages(newImageIds);
      self.render();
    });
  },
  render: function () {
    var self = this;
    if (!(self.addedTemplate)) {
      self.$el.html(isic.templates.imagesPage());
      self.$el.find('#histogramPane')[0]
        .appendChild(self.histogramPane.el);
      self.$el.find('#imageWall')[0]
        .appendChild(self.imageWall.el);
      self.addedTemplate = true;
    }
    self.histogramPane.render();
    self.imageWall.render();
  }
});

isic.router.route('images', 'images', function (id) {
    girder.events.trigger('g:navigateTo', isic.views.ImagesView);
});
