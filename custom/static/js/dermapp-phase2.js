'use strict';
/*global $, angular, ol, Mousetrap*/
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

            $rootScope.task_start = Date.now(); // global start time for this task

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
        $scope.annotation_model = {};
        $scope.annotation_options = undefined;

        $scope.selected_annotation = undefined;
        $scope.hover_annotation = undefined;

        $scope.certaintyModel = 'definite';

        $scope.showReview = false;
        $scope.filterval = '';

        $scope.formatter = new ol.format.GeoJSON();

        $rootScope.showingSegmentation = true;

        $rootScope.$watch('applicationReady', function () {
            if ($rootScope.applicationReady) {
                $scope.loadTasklist();
            }
        });

        $scope.selected = function () {
            $log.debug("selected", $scope.annotation_model);
        };

        $scope.loadTasklist = function () {
            var urlvals = window.location.pathname.split('/');
            var annotation_item_id = urlvals[urlvals.length - 1];
            $scope.annotation_item_id = annotation_item_id;

            var annotation_detail_url = '/api/v1/annotation/' + annotation_item_id;

            $http.get(annotation_detail_url).success(function (data) {
                //data.segmentation_info; // unused
                $scope.phase = 'Phase 2';
                $scope.current_image = data.image;
                $scope.annotation_options = data.variables;

                var segmentation_url = '/api/v1/item/' + $scope.current_image._id + '/segmentation';
                $rootScope.showingSegmentation = true;
                $rootScope.imageviewer.loadPainting(segmentation_url);
            });
        };

        $scope.hasValidTile = function (_id) {
            if (_id in $scope.annotation_model) {
                var tiles = $scope.annotation_model[_id];
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

            if (question_shortname in $scope.annotation_model) {
                $rootScope.imageviewer.loadTiles($scope.annotation_model[question_shortname]);
            }

            // label 2 -> 100%
            // label 3 -> 50%

//            $rootScope.imageviewer.selectAnnotationLabel($scope.certaintyModel);

        };

        $scope.selectTileAnnotation = function (theTile) {
            var question_shortname;
            // save the previous tile if anything is there

            if ($scope.selected_annotation) {

                var tiles = $rootScope.imageviewer.grabCurrentTiles().slice(0);

                question_shortname = $scope.selected_annotation.question.id;

                if (question_shortname in $scope.annotation_model) {
                    $scope.annotation_model[question_shortname] = tiles;
                } else {
                    $scope.annotation_model[question_shortname] = tiles;
                }

                $rootScope.imageviewer.clearTiles();
            }

            // now select the new tile

            $scope.selected_annotation = theTile;
            question_shortname = $scope.selected_annotation.question.id;

            if (question_shortname in $scope.annotation_model) {
                $rootScope.imageviewer.loadTiles($scope.annotation_model[question_shortname]);
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

        // shortcut key bindings -> takes you home to task list
        Mousetrap.bind( ['ctrl+q'], function (evt) {
            if (typeof (evt.preventDefault) === 'function') {
                evt.preventDefault();
            } else {
                evt.returnValue = false;
            }
            $scope.$apply();
        });

        // shortcut key bindings -> takes you home to task list
        Mousetrap.bind( ['space'], function (evt) {
            if (typeof (evt.preventDefault) === 'function') {
                evt.preventDefault();
            } else {
                evt.returnValue = false;
            }

            $scope.nextStep();
            $scope.$apply();
        });

        Mousetrap.bind( ['ctrl+z'], function (evt) {
            if (typeof (evt.preventDefault) === 'function') {
                evt.preventDefault();
            } else {
                evt.returnValue = false;
            }

            $scope.previousStep();
            $scope.$apply();
        });

        Mousetrap.bind( ['up'], function (evt) {
            if (typeof (evt.preventDefault) === 'function') {
                evt.preventDefault();
            } else {
                evt.returnValue = false;
            }
            $scope.increaseParameter();
            $scope.$apply();

        });

        Mousetrap.bind( ['down'], function (evt) {
            if (typeof (evt.preventDefault) === 'function') {
                evt.preventDefault();
            }
            else {
                evt.returnValue = false;
            }
            $scope.decreaseParameter();
            $scope.$apply();

        });

        $scope.reviewAnnotations = function () {
            if ($scope.selected_annotation) {

                var tiles = $rootScope.imageviewer.grabCurrentTiles().slice(0);

                var question_shortname = $scope.selected_annotation.question.id;

                if (question_shortname in $scope.annotation_model) {
                    $scope.annotation_model[question_shortname] = tiles;
                }
                else {
                    $scope.annotation_model[question_shortname] = tiles;
                }

                $scope.selected_annotation = undefined;

                $rootScope.imageviewer.clearTiles();
            }
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
            $log.debug( $scope );
            $log.debug('submit annotations happens here');

            var submit_url = '/api/v1/annotation/' + $scope.annotation_item_id;

            var taskcomplete_time = Date.now();

            var annotation_to_store = {
                'imageId' : $scope.current_image._id,
                'startTime' : $rootScope.task_start,
                'stopTime' : taskcomplete_time,
                'annotations': $scope.annotation_model
            };

            $http.put(submit_url, annotation_to_store).success(function () {
                window.location.replace('/uda/task');
            });
        };
    }
]);
