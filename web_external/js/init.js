/*global isic:true*/

var isic = isic || {};

_.extend(isic, {
    models: {},
    collections: {},
    views: {},
    util: {},
    router: new Backbone.Router(),
    events: girder.events
});

girder.router.enabled(false);
