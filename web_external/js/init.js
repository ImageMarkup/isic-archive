/*global isic_archive:true*/

var isic_archive = isic_archive || {};

_.extend(isic_archive, {
    models: {},
    collections: {},
    views: {},
    router: new Backbone.Router(),
    events: _.clone(Backbone.Events)
});

girder.router.enabled(false);
