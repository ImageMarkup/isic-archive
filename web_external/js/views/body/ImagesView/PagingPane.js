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
    if (!self.addedImages) {
      d3.select(this.el).selectAll('.button')
        .append('img')
        .attr('src', function () {
          var imgName = this.parentNode.getAttribute('id');
          return girder.staticRoot +
            '/built/plugins/isic_archive/extra/img/' +
            imgName + '.svg';
        });
      self.addedImages = true;
    }
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
