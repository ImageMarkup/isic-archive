'use strict';
/*global $, angular*/
/*jslint browser: true*/

// Initialization of angular root application
var derm_app = angular.module('DermApp', ['ui.bootstrap', 'ngSanitize', 'xml']);
derm_app.value("ol", ol);

derm_app.config(function ($httpProvider) {
    $httpProvider.defaults.xsrfCookieName = 'girderToken';
    $httpProvider.defaults.xsrfHeaderName = 'Girder-Token';
});

// Initialization of angular app controller with necessary scope variables. Inline declaration of external variables
// needed within the controller's scope. State variables (available between controllers using $rootScope). Necessary to
// put these in rootScope to handle pushed data via websocket service.
var appController = derm_app.controller('ApplicationController', ['$scope', '$rootScope', '$location', '$timeout', '$http', 'olViewer',
    function ($scope, $rootScope, $location, $timeout, $http, olViewer) {

        // global ready state variable
        $rootScope.applicationReady = false; // a hack to know when the rest has loaded (since ol3 won't init until dom does)
        $rootScope.imageviewer = undefined; // the ol3 viewer
        $scope.active_image = undefined; // image metedata for currently viewed image

        var api_user_url = '/api/v1/user/me';
        $rootScope.user = {};
        $http.get(api_user_url).success(function (data) {
            $rootScope.user = data;
        });

        // initial layout
        $("#angular_id").height(window.innerHeight);
        $("#map").height(window.innerHeight);

        $timeout(function () {
            $rootScope.ApplicationInit();
        }, 10);

        // main application, gives a bit of a delay before loading everything
        $rootScope.ApplicationInit = function () {
            $rootScope.debug  = $location.url().indexOf('debug') > -1;
            $rootScope.imageviewer = new olViewer({'div' : 'annotationView'});
            $rootScope.applicationReady = true;
        };

        $rootScope.$watch('active_image', function (newImage, oldValue) {
            if ($rootScope.applicationReady) {
                $rootScope.task_start = Date.now(); // global start time for this task
                $rootScope.imageviewer.clearCurrentImage();
                var image_url = '/api/v1/item/' + newImage._id;
                $rootScope.imageviewer.loadImageWithURL(image_url);
            }
        });

        $scope.safeApply = function (fn) {
            var phase = this.$root.$$phase;
            if (phase === '$apply' || phase === '$digest') {
                if (fn) { fn(); }
            } else {
                this.$apply(fn);
            }
        };
    }
]);
