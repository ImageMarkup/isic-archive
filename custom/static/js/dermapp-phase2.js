'use strict';
/*global $, angular, ol*/
/*jslint browser: true*/

// Initialization of angular root application
var derm_app = angular.module('DermApp', ['ui.bootstrap', 'ngSanitize', 'xml', 'ui.select']);
derm_app.value("ol", ol);

derm_app.config(function ($httpProvider, $logProvider) {
    $httpProvider.defaults.xsrfCookieName = 'girderToken';
    $httpProvider.defaults.xsrfHeaderName = 'Girder-Token';

    $logProvider.debugEnabled(true);
});

// Initialization of angular app controller with necessary scope variables. Inline declaration of external variables
// needed within the controller's scope. State variables (available between controllers using $rootScope). Necessary to
// put these in rootScope to handle pushed data via websocket service.
derm_app.controller('ApplicationController', ['$scope', '$rootScope', '$location', '$document', '$log', 'olViewer',
    function ($scope, $rootScope, $location, $document, $log, olViewer) {

        // global ready state variable
        $rootScope.applicationReady = false; // a hack to know when the rest has loaded (since ol3 won't init until dom does)
        $rootScope.imageviewer = undefined; // the ol3 viewer

        // initial layout
        $("#angular_id").height(window.innerHeight);
        $("#map").height(window.innerHeight);

        // main application, gives a bit of a delay before loading everything
        $document.ready(function () {
            $log.debug('DOM ready');
            $rootScope.imageviewer = new olViewer($('#map')[0]);
            $rootScope.applicationReady = true;

            updateLayout();
        });
    }
]);

derm_app.controller('UserController', ['$scope', '$http', '$log',
    function ($scope, $http, $log) {
        var apiUserUrl = '/api/v1/user/me';
        //$scope.user = {};
        $http.get(apiUserUrl).then(function (response) {
            $log.debug('Got user response', response);
            if (response.data) {
                $scope.user = response.data;
            } else {
                $scope.user = {
                    login: 'not logged in',
                    firstName: 'Anonymous',
                    lastName: ''
                };
            }
        });
    }
]);

derm_app.controller('AnnotationTool', ['$scope', '$rootScope', '$timeout', '$sanitize', '$http', '$modal', '$log',
    function ($scope, $rootScope, $timeout, $sanitize, $http, $modal, $log) {
        $scope.annotation_values = {};
        $scope.annotation_options = undefined;

        $scope.selected_question_id = undefined;

        $scope.certaintyModel = 'definite';
        $scope.phase = 'Phase 2';

        $scope.showReview = false;
        $scope.filterval = '';

        $rootScope.showingSegmentation = true;

        $rootScope.$watch('applicationReady', function () {
            if ($rootScope.applicationReady) {
                loadAnnotationTask();
            }
        });

        $scope.selected = function () {
            $log.debug("selected", $scope.annotation_values);
        };

        function loadAnnotationTask () {
            var urlvals = window.location.pathname.split('/');
            var annotation_item_id = urlvals[urlvals.length - 1];
            $scope.annotation_item_id = annotation_item_id;

            var annotation_detail_url = '/api/v1/annotation/' + annotation_item_id;
            $http.get(annotation_detail_url).success(function (data) {
                //data.segmentation_info; // unused
                $scope.current_image = data.image;
                $scope.annotation_options = data.variables;

                var segmentation_url = '/api/v1/item/' + $scope.current_image._id + '/segmentation';
                $rootScope.showingSegmentation = true;
                $rootScope.imageviewer.loadPainting(segmentation_url);
                $scope.task_start = Date.now(); // global start time for this task
            });
        }

        $scope.hasValidTile = function (_id) {
            if (_id in $scope.annotation_values) {
                var tiles = $scope.annotation_values[_id];
                for (var i=0;i<tiles.length;i++) {
                    if (tiles[i] > 0)
                    {
                        return true;
                    }
                }
            }
            return false;
        };

        $scope.resetTiles = function () {
            if ($rootScope.imageviewer) {
                $rootScope.imageviewer.clearTiles();
            }
        };

        $scope.hoverTiles = function (theTile) {
            $rootScope.imageviewer.clearTiles();

            var question_shortname = theTile.id;

            if (question_shortname in $scope.annotation_values) {
                $rootScope.imageviewer.loadTiles($scope.annotation_values[question_shortname]);
            }

            // label 2 -> 100%
            // label 3 -> 50%

//            $rootScope.imageviewer.selectAnnotationLabel($scope.certaintyModel);

        };

        function storeSelectedQuestion () {
            if ($scope.selected_question_id) {
                $scope.annotation_values[$scope.selected_question_id] =
                    $rootScope.imageviewer.grabCurrentTiles().slice(0);

                $scope.selected_question_id = undefined;
                $rootScope.imageviewer.clearTiles();
            }
        }

        $scope.selectQuestion = function (question_id) {
            storeSelectedQuestion();

            $scope.selected_question_id = question_id;
            if ($scope.selected_question_id in $scope.annotation_values) {
                $rootScope.imageviewer.loadTiles($scope.annotation_values[$scope.selected_question_id]);
            }

            // label 2 -> 100%
            // label 3 -> 50%
            $rootScope.imageviewer.selectAnnotationLabel($scope.certaintyModel);
        };

        $scope.$watch('certaintyModel', function (newValue, oldValue) {
            if (newValue) {
                if ($rootScope.imageviewer) {
                    $rootScope.imageviewer.selectAnnotationLabel(newValue);
                }
            }
        });

        $scope.reviewAnnotations = function () {
            storeSelectedQuestion();
            $scope.showReview = true;
        };

        $scope.hideReview = function () {
           $rootScope.imageviewer.clearTiles();

            // label 2 -> 100%
            // label 3 -> 50%

            $rootScope.imageviewer.selectAnnotationLabel($scope.certaintyModel);

            $scope.showReview = false;
        };

        $scope.submitAnnotations = function () {
            var submit_url = '/api/v1/annotation/' + $scope.annotation_item_id;
            var annotation_to_store = {
                'imageId' : $scope.current_image._id,
                'startTime' : $scope.task_start,
                'stopTime' : Date.now(),
                'annotations': $scope.annotation_values
            };
            $http.put(submit_url, annotation_to_store).success(function () {
                window.location.replace('/uda/task');
            });
        };
    }
]);
