'use strict';

// Initialization of root Angular application
angular.module('DermApp',
    // Dependencies
    [
        'mousetrap',
        'ui.bootstrap',
        'ngSanitize',
        'xml',
        'ui.select',
        'frapontillo.bootstrap-switch'
    ],
    // Config
    function ($httpProvider, $logProvider) {
        $httpProvider.defaults.xsrfCookieName = 'girderToken';
        $httpProvider.defaults.xsrfHeaderName = 'Girder-Token';

        $logProvider.debugEnabled(false);
    }
);
