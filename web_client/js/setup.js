/**
 * Add a link to the Task Dashboard on the main Girder nav panel.
 */
girder.wrap(girder.views.LayoutGlobalNavView, 'render', function (render) {
    if (girder.currentUser) {
        this.defaultNavItems.unshift({
            name: 'Image Tasks',
            icon: 'icon-picture',
            target: 'uda-tasks'
        });
    }

    render.call(this);
});

girder.router.route('uda-tasks', 'uda-tasks', function () {
    window.location.replace('/uda/task');
});
