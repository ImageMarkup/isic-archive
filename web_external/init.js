/*global isic:true*/

var isic = isic || {};

_.extend(isic, {
    models: {},
    collections: {},
    views: {},
    router: new Backbone.Router(),
    events: girder.events
});

girder.router.enabled(false);
