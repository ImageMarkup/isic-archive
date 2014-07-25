/**
 * Created by stonerri on 7/25/14.
 */

girder.wrap(girder.views.HierarchyWidget, 'render', function (render) {
    // Call the underlying render function that we are wrapping
    render.call(this);

    // Add a link just below the widget
    this.$('li a.g-edit-folder').after('<a class="qc-link"><i class="icon-thumbs-up"></i>Run QC</a>');
});


girder.views.HierarchyWidget.prototype.events['click a.qc-link'] = function () {

    window.open(
      '/uda/qc/' + this.parentModel.get('_id'),
      '_blank'
    );
};