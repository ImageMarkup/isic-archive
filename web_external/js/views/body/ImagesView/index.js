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
    self.imageDetailsPane = new isic.views.ImagesSubViews.ImageDetailsPane();

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
        self.imageDetailsPane.updateDetails(imageId);
        self.render();
      });

    self.listenTo(self.pagingPane, 'iv:toggleHistogram',
      function () {
        // Regardless of whether this goes on or off,
        // we want to remove hide the selected item details
        // (i.e. if we're turning it off, we want to close
        // the sidebar. If we're turning it on, we want to
        // show the histograms, not the individual selection)
        self.imageWall.selectImage(null);
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
      self.$el.html(isic.templates.imagesPage());
      recolorImageFilters(['#00ABFF', '#444499']);
      self.histogramPane.setElement(self.$el.find('#isic-images-histogramPane')[0]);
      self.histogramPane.addedDomListeners = false;
      self.imageWall.setElement(self.$el.find('#isic-images-imageWall')[0]);
      self.imageWall.addedDomListeners = false;
      self.pagingPane.setElement(self.$el.find('#isic-images-pagingPane')[0]);
      self.pagingPane.addedDomListeners = false;
      self.imageDetailsPane.setElement(self.$el.find('#isic-images-imageDetailsPane')[0]);
      self.imageDetailsPane.addedDomListeners = false;
      self.addedTemplate = true;
    }
    self.imageWall.render();
    self.pagingPane.render();

    // Only show either the histogram or selected pane at a time
    // (don't show both)
    if (self.imageWall.selectedImageId) {
      self.$el.find('#isic-images-imageDetailsPane').css('display', '');
      self.imageDetailsPane.render();

      self.$el.find('#isic-images-histogramPane').css('display', 'none');
    } else {
      self.$el.find('#isic-images-imageDetailsPane').css('display', 'none');

      if (self.pagingPane.showHistograms) {
        self.$el.find('#isic-images-histogramPane').css('display', '');
        self.histogramPane.render();
      } else {
        self.$el.find('#isic-images-histogramPane').css('display', 'none');
      }
    }
  }
});

isic.router.route('images', 'images', function (id) {
    girder.events.trigger('g:navigateTo', isic.views.ImagesView);
});
