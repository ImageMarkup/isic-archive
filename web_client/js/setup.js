/*global girder*/

/**
 * Add a link to the Task Dashboard on the main Girder nav panel.
 */
girder.wrap(girder.views.LayoutGlobalNavView, 'render', function (render) {
    'use strict';

    this.navItems = [
        {
            name: 'Lesion Datasets',
            icon: 'icon-picture',
            target: 'isic-datasets'
        },
        {
            name: 'Annotation Studies',
            icon: 'icon-eye',
            target: 'isic-studies'
        }
    ];
    if (girder.currentUser) {
        this.navItems.push({
            name: 'Your Tasks',
            icon: 'icon-check',
            target: 'isic-tasks'
        });
    }
    this.navItems = this.navItems.concat(this.defaultNavItems);
    if (girder.currentUser && girder.currentUser.get('admin')) {
        this.navItems.push({
            name: 'Admin console',
            icon: 'icon-wrench',
            target: 'admin'
        });
    }

    render.call(this);
    return this;
});

function _navigateToCollection(collectionName, replace) {
    girder.restRequest({
        path: '/resource/lookup',
        data: {'path': '/collection/' + collectionName},
        type: 'GET'
    }).done(function (response) {
        var imagesCollectionId = response._id;
        // TODO: handle missing collection
        girder.router.navigate('collection/' + imagesCollectionId, {
            trigger: true,
            replace: replace
        });
    });
}

girder.router.route('isic-studies', 'isic-studies', function () {
    'use strict';
    window.location.replace('/uda/multirater');
});

girder.router.route('isic-tasks', 'isic-tasks', function () {
    'use strict';
    window.location.replace('/uda/task');
});
