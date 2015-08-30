'use strict';
/*global angular, ol, Mousetrap, console*/
/*jslint browser: true*/

// Initialization of angular root application
var derm_app = angular.module('DermApp', ['ui.bootstrap', 'ngSanitize', 'xml', 'ui.select']);
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
        $http.get(api_user_url).then(function (response) {
            $rootScope.user = response.data;
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

            $rootScope.task_start = Date.now(); // global start time for this task

            updateLayout();
        };

        $rootScope.$watch('active_image', function (newImage, oldValue) {
            if ($rootScope.applicationReady) {
                $rootScope.imageviewer.clearCurrentImage();
                var image_url = '/api/v1/item/' + newImage._id;
                $rootScope.imageviewer.loadImageWithURL(image_url);
            }
        });

        $scope.safeApply = function (fn) {
            var phase = this.$root.$$phase;
            if (phase === '$apply' || phase === '$digest') {
                if (fn) {
                    fn();
                }
            } else {
                this.$apply(fn);
            }
        };
    }
]);


var annotationTool = derm_app.controller('AnnotationTool', ['$scope', '$rootScope', '$timeout', '$sanitize', '$http', '$modal', '$log',
    function ($scope, $rootScope, $timeout, $sanitize, $http, $modal, $log) {
        $scope.annotation_model = {};
        $scope.annotation_options = undefined;
        $scope.annotation_source = undefined;

        $scope.selected_annotation = undefined;
        $scope.hover_annotation = undefined;

        $scope.certaintyModel = 'definite';

        $scope.showReview = false;
        $scope.filterval = '';

        $scope.formatter = new ol.format.GeoJSON();

        $rootScope.showingSegmentation = true;

        $rootScope.$watch('user', function (newUser, oldUser) {
            if (newUser._id) {
                $scope.loadTasklist();
            }
        });

        $scope.selected = function() {
            console.log("selected", $scope.annotation_model);
        };

        $scope.loadTasklist = function () {
            var urlvals = window.location.pathname.split('/');
            var annotation_item_id = urlvals[urlvals.length - 1];
            $scope.annotation_item_id = annotation_item_id;

            var annotation_detail_url = '/api/v1/annotation/' + annotation_item_id;

            $http.get(annotation_detail_url).success(function (data) {
                $scope.current_annotation = null; // TODO
                $scope.decision_tree = data.decision_tree;
                $scope.phase = 'Phase 2';
                $scope.totalSteps = $scope.decision_tree.length;
                $scope.annotation_source = data.annotation;
                $scope.current_image = data.image;
                $scope.annotation_options = data.variables;

                var segmentation_url = '/api/v1/item/' + $scope.current_image._id + '/segmentation';
                $rootScope.showingSegmentation = true;
                $rootScope.imageviewer.loadPainting(segmentation_url);
            });
        };

        $scope.getCurrentAnnotation = function () {

            if ($rootScope.applicationReady) {
                return $scope.current_annotation;
            }
            return undefined;
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
            console.log( $scope );
            console.log('submit annotations happens here');

            //var submit_url = '/api/v1/annotation/' + $scope.current_annotation._id;
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


        // setters

        $scope.saveCurrentStepAnnotation = function () {

            // just making things explicit for readability's sake
            var features = $rootScope.imageviewer.getFeatures();

            console.log('current step features', features);

            var submitTime = Date.now();

            var current_step = $scope.step;

            if (features.length) {

                if ($scope.step_config && $scope.step_config.type) {
                    var geojsonfeatures;
                    var singleAnnotation;

                    // if we're in teh superpixel mode, discard the placehold feature and make your own from the external parameters
                    // ugly but it should work.
                    if ($scope.step_config.type === 'superpixel') {

                        var segmentationPackage = $rootScope.imageviewer.getSegmentationPackage();

                        var feature = new ol.Feature({
                            title: 'superpixel',
                            longtitle: 'superpixel region',
                            icon: '',
                            source: $scope.phase,
                            parameters: segmentationPackage
                        });

                        // set the geometry of this feature to be the screen extents
                        feature.setGeometry(new ol.geom.Point([0, 0]));

                        geojsonfeatures = $scope.formatter.writeFeatures([feature]);

                        singleAnnotation = {
                            markup : geojsonfeatures,
                            startTime : $scope.step_start,
                            submitTime : submitTime
                        };

                        $scope.current_annotation.steps[current_step] = singleAnnotation;
                    }
                    else if (current_step in Object.keys($scope.current_annotation.steps)) {

                        // we have an existing annotation, just update the features and modify date
                        //var stepAnnotation = currentAnnotation.steps[current_step]

                        //var geojson  = new ol.parser.GeoJSON;
                        //var features = vectorsource.getFeatures();
                        //var json     = geojson.writeFeatures(features);

                        geojsonfeatures = $scope.formatter.writeFeatures(features);

                        singleAnnotation = {
                            markup : geojsonfeatures,
                            startTime : $scope.step_start,
                            submitTime : submitTime
                        };

                        $scope.current_annotation.steps[current_step] = singleAnnotation;

                    }
                    else {
                        // this is the first instance of the annotation, set the create date and field of view as well
                        console.log('this is the first annotation for this step, creating');

                        geojsonfeatures = $scope.formatter.writeFeatures(features);

                        singleAnnotation = {
                            markup : geojsonfeatures,
                            startTime : $scope.step_start,
                            submitTime : submitTime
                        };

                        $scope.current_annotation.steps[current_step] = singleAnnotation;
                    }
                }
            }
            else {
                console.log('don\'t show up here');
            }
            console.log($scope.current_annotation);
        };
    }
]);
