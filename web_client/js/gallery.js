
// Gallery

girder.wrap(girder.views.HierarchyWidget, 'render', function (render) {
    // Call the underlying render function that we are wrapping
    render.call(this);

    // Add a link just below the widget
    this.$('li a.g-edit-folder').after('<a class="gallery-link"><i class="icon-th"></i>Open as gallery</a>');
});


girder.views.HierarchyWidget.prototype.events['click a.gallery-link'] = function () {

    window.open(
      '/uda/gallery/' + this.parentModel.get('_id'),
      '_blank'
    );
};

