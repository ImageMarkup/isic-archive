/*globals girder, jQuery, d3, Image, backbone*/
/*eslint-disable*/

isic.views.ImagesSubViews = isic.views.ImagesSubViews || {};

isic.views.ImagesSubViews.PagingPane = Backbone.View.extend({
  initialize: function () {
    var self = this;
    self.showHistograms = false;
  },
  render: function () {
    var self = this;
    if (!self.addedDomListeners) {
      self.$el.find('#toggleHistogram').on('click', function () {
        self.showHistograms = !self.showHistograms;
        self.trigger('iv:toggleHistogram');
      });
      self.addedDomListeners = true;
    }

    if (self.showHistograms) {
      self.$el.find('#toggleHistogram').addClass('selected');
    } else {
      self.$el.find('#toggleHistogram').removeClass('selected');
    }
  }
});
