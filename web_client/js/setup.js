/*global girder*/

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
    'use strict';
    }

    render.call(this);
});

girder.router.route('uda-tasks', 'uda-tasks', function () {
    'use strict';
    window.location.replace('/uda/task');
});
