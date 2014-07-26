/**
 * Created by stonerri on 7/25/14.
 */

// Gallery

girder.wrap(girder.views.LayoutHeaderUserView, 'render', function (render) {
    // Call the underlying render function that we are wrapping
    render.call(this);

    // Add a link just below the widget
    this.$('li a.g-my-folders').after('<a class="a-mytasks-link"><i class="icon-th-list"></i>My tasks</a>');
});


girder.views.LayoutHeaderUserView.prototype.events['click a.a-mytasks-link'] = function () {

    window.open(
      '/uda/task/' + girder.currentUser.get('_id'),
      '_blank'
    );
};

