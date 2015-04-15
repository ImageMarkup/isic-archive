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


girder.wrap(girder.views.LayoutGlobalNavView, 'render', function (render) {
    render.call(this);

    if (girder.currentUser) {
        this.$('ul.g-global-nav').prepend('<li class="g-global-nav-li" style="background-color: #7edba9"><a href="/uda/task" g-name="Collections" class="g-nav-link"><i class="icon-picture"></i><span>Image Tasks</span></a></li>');
    }
});


girder.views.LayoutHeaderUserView.prototype.events['click a.a-mytasks-link'] = function () {
    window.open(
      '/uda/task',
      '_blank'
    );
};

