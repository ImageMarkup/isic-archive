/*global girder*/

girder.wrap(girder.views.HierarchyWidget, 'render', function (render) {
    'use strict';
    // Call the underlying render function that we are wrapping
    render.call(this);

    // Add a link just below the widget
    this.$('li a.g-edit-folder').after('<a class="qc-link"><i class="icon-thumbs-up"></i>Run QC</a>');
});


girder.views.HierarchyWidget.prototype.events['click a.qc-link'] = function () {
    'use strict';
    window.open(
        '/uda/qc/' + this.parentModel.get('_id'),
        '_blank'
    );
};
