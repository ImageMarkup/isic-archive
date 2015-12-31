'use strict';
/*global $, angular, ol*/
/*jslint browser: true*/

// Initialization of angular root application
var derm_app = angular.module('DermApp');

// Register 'ol' service
derm_app.value('ol', ol);

// Initialization of angular app controller with necessary scope variables. Inline declaration of external variables
// needed within the controller's scope. State variables (available between controllers using $rootScope). Necessary to
// put these in rootScope to handle pushed data via websocket service.
derm_app.controller('ApplicationController',
    ['$scope', '$rootScope', '$location', '$document', '$log', 'olViewer',
    function ($scope, $rootScope, $location, $document, $log, olViewer) {

        // global ready state variable
        $rootScope.applicationReady = false; // a hack to know when the rest has loaded (since ol3 won't init until dom does)
        $rootScope.imageviewer = undefined; // the ol3 viewer

        // initial layout
        $("#angular_id").height(window.innerHeight);
        $("#map").height(window.innerHeight);

        // main application, gives a bit of a delay before loading everything
        $document.ready(function () {
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

derm_app.controller('AnnotationController', ['$scope', '$rootScope', '$location', '$http', '$log',
    function ($scope, $rootScope, $location, $http, $log) {
        $rootScope.showingSegmentation = true;

        $scope.overview_image_url = null;
        $scope.display_overview = true;

        $scope.annotation_values = {};
        $scope.clearAnnotations = function () {
            // annotation_values should be set before initialization,
            //   but must also be re-cleared after child controllers run
            $scope.$broadcast('reset');
            $scope.annotation_values = {};
            $scope.showReview = false;
        };

        $rootScope.$watch('applicationReady', function (ready) {
            if (ready === true) {
                $scope.annotation_item_id = $location.path().substring(1);
            }
        });

        var image_item_id;
        var start_time;
        $scope.$watch('annotation_item_id', function (annotation_item_id) {
            if (annotation_item_id !== undefined) {
                var annotation_detail_url = '/api/v1/annotation/' + annotation_item_id;
                $http.get(annotation_detail_url).success(function (data) {
                    $scope.all_features = data.features;

                    image_item_id = data.image._id;
                    $rootScope.imageviewer.loadPainting(
                        image_item_id,
                        data.segmentationId,
                        function () {
                            // this callback is being executed from non-Angular code, so we must
                            //   wrap all work that it does in an $apply
                            $scope.$apply(function () {
                                $scope.clearAnnotations();
                            });
                        }
                    );

                    var image_detail_url = '/api/v1/image/' + image_item_id;
                    $http.get(image_detail_url).success(function (data) {
                        $scope.image_info = data;
                    });

                    $scope.overview_image_url = '/api/v1/image/' + image_item_id + '/thumbnail?width=256';

                    start_time = Date.now();
                });
            }
        });

        /* Submit an annotation task.
         *
         * status should be either 'true', or a string describing the reason
         * for failure.
         */
        $scope.submitAnnotations = function (status) {
            var submit_url = '/api/v1/annotation/' + $scope.annotation_item_id;
            var annotation_to_store = {
                status: status === true ? 'ok' : status,
                imageId: image_item_id,
                startTime: start_time,
                stopTime: Date.now(),
                annotations: $scope.annotation_values
            };
            $http.put(submit_url, annotation_to_store).success(function () {
                window.location.replace('/uda/task');
            });
        };
    }
]);


derm_app.controller('FlagAnnotationController', ['$scope', '$log',
    function ($scope, $log) {
        $scope.flag = function (reason) {
            $scope.clearAnnotations();
            $scope.submitAnnotations(reason);
        };
    }
]);


derm_app.controller('ImageFeatureAnnotationController', ['$scope', '$log',
    function ($scope, $log) {
        $scope.$watch('all_features', function (all_features) {
            if (all_features !== undefined) {
                $scope.features = all_features.lesionlevel;
            }
        });

        $scope.$on('reset', function () {
            // will also be called to initialize
            // TODO: reset drop-downs
        });

        $scope.selected = function () {
            $log.debug("selected", $scope.annotation_values);
        };
    }
]);

derm_app.controller('RegionFeatureAnnotationController', ['$scope', '$rootScope', '$log',
    function ($scope, $rootScope, $log) {
        $scope.$watch('all_features', function (all_features) {
            $log.debug('RegionFeatureAnnotationController.all_features', all_features);
            if (all_features !== undefined) {
                $scope.features = all_features.tiles;
            }
        });

        $scope.$on('reset', function () {
            $log.debug('RegionFeatureAnnotationController.reset');
            // will also be called to initialize
            $scope.selected_question_id = undefined;
            // TODO: if annotation_values were specific to this scope, we could clear it here
            $scope.certaintyModel = 'definite';
            $scope.filterval = '';
        });

        $scope.$watch('selected_question_id', function (new_question_id, old_question_id) {
            $log.debug('RegionFeatureAnnotationController.selected_question_id', old_question_id, new_question_id);
            // TODO: ensure that new_question_id is actually in $scope.annotation_options
            // store the previously selected feature
            if (old_question_id !== undefined) {
                // TODO: don't store when in review mode
                $scope.annotation_values[old_question_id] =
                    $rootScope.imageviewer.grabCurrentTiles().slice(0);
            }
            // reset the overlay
            if ($rootScope.imageviewer) {
                $rootScope.imageviewer.clearTiles();
            }
            // load any already-stored feature data
            if (new_question_id in $scope.annotation_values) {
                $rootScope.imageviewer.loadTiles($scope.annotation_values[$scope.selected_question_id]);
            } else if (new_question_id === undefined) {
                // TODO: disable annotation layer interaction (but not display)
            }
        });

        $scope.$watch('certaintyModel', function (certaintyModel) {
            $log.debug('RegionFeatureAnnotationController.certaintyModel', certaintyModel);
            if (certaintyModel !== undefined) {
                if ($rootScope.imageviewer) {
                    // label 2 -> 100%
                    // label 3 -> 50%
                    $rootScope.imageviewer.selectAnnotationLabel(certaintyModel);
                }
            }
        });

        $scope.$watch('showReview', function (showReview) {
            $log.debug('RegionFeatureAnnotationController.showReview', showReview);
            if (showReview === true) {
                // this will clear the tiles
                $scope.selected_question_id = undefined;
            } else if (showReview === false) {
                if ($rootScope.imageviewer) {
                    $rootScope.imageviewer.clearTiles();
                }
            }
        });

        $scope.selectQuestion = function (question_id) {
            $log.debug('RegionFeatureAnnotationController.selectQuestion', question_id);
            $scope.selected_question_id = question_id;
            // TODO: selectAnnotationLabel may not be necessary
            $rootScope.imageviewer.selectAnnotationLabel($scope.certaintyModel);
        };

        $scope.questionHasPositiveTile = function (question_id) {
            // TODO: this is being called way too much
            var result;
            var feature_value = $scope.annotation_values[question_id];
            if (Array.isArray(feature_value)) {
                result = feature_value.some(function (tile_val) {
                    return tile_val !== 0;
                });
            } else {
                result = false;
            }
            return result;
        };

        $scope.displayQuestionTiles = function (question_id) {
            // TODO: just set $scope.selected_question_id, but update that watch function to not store annotations in review mode
            $rootScope.imageviewer.clearTiles();
            if (question_id in $scope.annotation_values) {
                $rootScope.imageviewer.loadTiles($scope.annotation_values[question_id]);
            }
            //$rootScope.imageviewer.selectAnnotationLabel($scope.certaintyModel);
        };
    }
]);
