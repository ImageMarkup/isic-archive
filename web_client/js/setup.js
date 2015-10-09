/*global girder*/

/**
 * Add a link to the Task Dashboard on the main Girder nav panel.
 */
girder.wrap(girder.views.LayoutGlobalNavView, 'render', function (render) {
    'use strict';

    var isicNavItems = [
        {
            name: 'Lesion Images',
            icon: 'icon-picture',
            target: 'isic-images'
        },
        {
            name: 'Annotation Studies',
            icon: 'icon-eye',
            target: 'isic-studies'
        }
    ];
    if (girder.currentUser) {
        isicNavItems.push({
            name: 'Your Tasks',
            icon: 'icon-check',
            target: 'isic-tasks'
        });
    }
    this.navItems = isicNavItems.concat(this.defaultNavItems);

    render.call(this);
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

girder.router.route('isic-images', 'isic-images', function () {
    'use strict';
    _navigateToCollection('Lesion Images', true);
});

girder.router.route('isic-studies', 'isic-studies', function () {
    'use strict';
    _navigateToCollection('Annotation Studies', true);
});

girder.router.route('isic-tasks', 'isic-tasks', function () {
    'use strict';
    window.location.replace('/uda/task');
});
