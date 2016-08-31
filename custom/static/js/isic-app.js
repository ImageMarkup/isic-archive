'use strict';

// Initialization of root Angular application
var isicApp = angular.module('DermApp',
    // Dependencies
    [
        'ngResource',
        'mousetrap',
        'ui.bootstrap',
        'ngSanitize',
        'frapontillo.bootstrap-switch'
    ],
    // Config
    function ($httpProvider, $logProvider) {
        $httpProvider.defaults.xsrfCookieName = 'girderToken';
        $httpProvider.defaults.xsrfHeaderName = 'Girder-Token';

        $logProvider.debugEnabled(false);
    }
);

isicApp.factory('User', function ($resource) {
    return $resource('/api/v1/user/:id',  {id: 'me'});
});

isicApp.factory('Dataset', function ($resource) {
    return $resource('/api/v1/dataset/:id', {id: '@_id'});
});

isicApp.factory('Image', function ($resource) {
    return $resource('/api/v1/image/:id', {id: '@_id'});
});

isicApp.factory('Segmentation', function ($resource) {
    return $resource('/api/v1/segmentation/:id', {id: '@_id'});
});

isicApp.factory('Study', function ($resource) {
    return $resource('/api/v1/study/:id', {id: '@_id'});
});

isicApp.factory('Featureset', function ($resource) {
    return $resource('/api/v1/featureset/:id', {id: '@_id'});
});

isicApp.factory('Annotation', function ($resource) {
    return $resource('/api/v1/annotation/:id', {id: '@_id'});
});
