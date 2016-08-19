/*globals girder, jQuery, d3, Image, backbone*/
/*eslint-disable*/

isic.views.ImagesSubViews = isic.views.ImagesSubViews || {};

isic.views.ImagesSubViews.ImageDetailsPane = Backbone.View.extend({
  initialize: function () {
    var self = this;
    self.details = {};
  },
  updateDetails: function (imageId) {
    // TODO: display the image and its metadata
    this.$el.html('<p>Selected image:</p><pre>' + imageId + '</pre>');
  },
  render: function () {

  }
});
