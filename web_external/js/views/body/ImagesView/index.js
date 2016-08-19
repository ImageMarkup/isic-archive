/*globals girder, jQuery, d3, Image*/
/*eslint-disable*/

isic.views.ImagesSubViews = isic.views.ImagesSubViews || {};

isic.views.ImagesView = isic.View.extend({
  initialize: function () {
    var self = this;
    // Initialize our subviews
    self.histogramPane = new isic.views.ImagesSubViews.HistogramPane();
    self.imageWall = new isic.views.ImagesSubViews.ImageWall();
    self.pagingPane = new isic.views.ImagesSubViews.PagingPane();

    window.onresize = function () {
      self.render();
    };
    self.attachListeners();
    self.updateCurrentPage();
  },
  attachListeners: function () {
    var self = this;
    self.listenTo(self.histogramPane, 'iv:changeFilters',
      function () {
        self.updateCurrentPage();
      });

    self.listenTo(self.imageWall, 'iv:selectImage',
      function (imageId) {
        self.selectImage(imageId);
      });

    self.listenTo(self.pagingPane, 'iv:toggleHistogram',
      function () {
        self.render();
      });
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
      self.$el.html(isic.templates.imagesPage({
          staticRoot: girder.staticRoot,
      }));
      self.histogramPane.setElement(self.$el.find('#histogramPane')[0]);
      self.histogramPane.addedDomListeners = false;
      self.imageWall.setElement(self.$el.find('#imageWall')[0]);
      self.imageWall.addedDomListeners = false;
      self.pagingPane.setElement(self.$el.find('#pagingPane')[0]);
      self.pagingPane.addedDomListeners = false;
      self.addedTemplate = true;
    }
    self.histogramPane.render();
    self.imageWall.render();
    self.pagingPane.render();

    self.$el.find('#histogramPane')
      .css('display', self.pagingPane.showHistograms ? '' : 'none');
  }
});

isic.router.route('images', 'images', function (id) {
    girder.events.trigger('g:navigateTo', isic.views.ImagesView);
});
