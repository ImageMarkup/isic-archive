'use strict';
/*global $, angular, ol*/
/*jslint browser: true*/

var derm_app = angular.module('DermApp');

// Initialization of angular app controller with necessary scope variables. Inline declaration of external variables
// needed within the controller's scope. State variables (available between controllers using $rootScope). Necessary to
// put these in rootScope to handle pushed data via websocket service.
derm_app.controller('ApplicationController',
    ['$scope', '$rootScope', '$location', '$document', '$log',
    function ($scope, $rootScope, $location, $document, $log) {

        // global ready state variable
        $rootScope.applicationReady = false; // a hack to know when the rest has loaded (since ol3 won't init until dom does)
        $rootScope.imageviewer = undefined; // the ol3 viewer

        // initial layout
        $("#angular_id").height(window.innerHeight);
        $("#map").height(window.innerHeight);

        // main application, gives a bit of a delay before loading everything
        $document.ready(function () {
            $rootScope.imageviewer = new PixelMap($('#map')[0]);
            $rootScope.applicationReady = true;

            updateLayout();
        });
    }
]);

derm_app.controller('AnnotationController', [
    '$scope', '$rootScope', '$location', '$http', '$log',
    'Annotation', 'Study', 'Featureset', 'Image',
    function ($scope, $rootScope, $location, $http, $log,
              Annotation, Study, Featureset, Image) {
        $scope.annotation_values = {};
        $scope.clearAnnotations = function () {
            // annotation_values should be set before initialization,
            //   but must also be re-cleared after child controllers run
            $scope.$broadcast('reset');
            $scope.annotation_values = {};
            $scope.showReview = false;
        };

        $rootScope.$watch('applicationReady', function () {
            if ($scope.applicationReady) {
                $scope.annotation_id = $location.path().substring(1);
            }
        });

        $scope.$watch('annotation_id', function () {
            if (!$scope.annotation_id) {
                return;
            }
            $scope.annotation = Annotation.get({'id': $scope.annotation_id});
        });

        var start_time;
        $scope.$watch('annotation && annotation._id', function () {
            if (!$scope.annotation || !$scope.annotation.$resolved) {
                return;
            }
            $scope.study = Study.get({'id': $scope.annotation.studyId});
            $scope.image = Image.get({'id': $scope.annotation.image._id});

            $rootScope.imageviewer.loadImage(
                $scope.annotation.image._id,
                function () {
                    // this callback is being executed from non-Angular code, so we must
                    //   wrap all work that it does in an $apply
                    $scope.$apply(function () {
                        $scope.clearAnnotations();
                    });
                }
            );
            start_time = Date.now();
        });
        $scope.$watch('study && study._id', function () {
            if (!$scope.study || !$scope.study.$resolved) {
                return;
            }
            $scope.featureset = Featureset.get({'id': $scope.study.featureset._id});
        });

        /* Submit an annotation task.
         *
         * status should be either 'true', or a string describing the reason
         * for failure.
         */
        $scope.submitAnnotations = function (status) {
            var normalized_annotation_values = angular.copy($scope.annotation_values);
            delete normalized_annotation_values[null]; // This somehow is getting added
            angular.forEach(normalized_annotation_values, function (feature_value, feature_id) {
                if (Array.isArray(feature_value)) {
                    normalized_annotation_values[feature_id] = feature_value.map(function (superpixel_value) {
                        if (superpixel_value === 0) {
                            return 0;
                        }
                        else if (superpixel_value === 2) {
                            return 1.0;
                        }
                        else if (superpixel_value === 3) {
                            return 0.5;
                        }
                        return null;
                    });
                }
            });

            var submit_url = '/api/v1/annotation/' + $scope.annotation._id;
            var annotation_to_store = {
                status: status === true ? 'ok' : status,
                imageId: $scope.image._id,
                startTime: start_time,
                stopTime: Date.now(),
                annotations: normalized_annotation_values
            };
            $http.put(submit_url, annotation_to_store).success(function () {
                //window.location.replace('/#tasks');
                // TODO: this won't work if study has no more annotations
                window.location.replace('/api/v1/task/me/annotation/redirect?studyId=' + $scope.study._id);
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


derm_app.controller('GlobalFeatureAnnotationController', ['$scope', '$log',
    function ($scope, $log) {
        $scope.$watch('featureset && featureset._id', function () {
            if (!$scope.featureset || !$scope.featureset.$resolved) {
                return;
            }
            // TODO: reset
        });

        $scope.$on('reset', function () {
            // will also be called to initialize
            // TODO: reset drop-downs
        });

        $scope.feature_selected_option_name = function (feature) {
            var selected_option_id = $scope.annotation_values[feature.id];
            var selected_option = feature.options.find(function (option) {
                return option.id === selected_option_id;
            });
            return selected_option ? selected_option.name : "";
        };

        $scope.selected = function () {
            $log.debug("selected", $scope.annotation_values);
        };
    }
]);

derm_app.controller('LocalFeatureAnnotationController', ['$scope', '$rootScope', '$log',
    function ($scope, $rootScope, $log) {
        $scope.$watch('featureset && featureset._id', function () {
            if (!$scope.featureset || !$scope.featureset.$resolved) {
                return;
            }
            $scope.feature_groups = {};
            $scope.featureset.localFeatures.forEach(function (feature) {
                if (!$scope.feature_groups.hasOwnProperty(feature.name[0])) {
                    $scope.feature_groups[feature.name[0]] = [];
                }
                $scope.feature_groups[feature.name[0]].push(feature);
            });
        });

        // Manually initialize variables as a hack to deal with event race conditions
        $scope.certaintyModel = 'definite';
        $scope.$on('reset', function () {
            // will also be called to initialize
            $scope.selected_feature_id = null;
            // TODO: if annotation_values were specific to this scope, we could clear it here
            $scope.certaintyModel = 'definite';
            $scope.filterval = '';
        });

        $scope.$watch('selected_feature_id', function (new_feature_id, old_feature_id) {
            // store the previously selected feature
            if (old_feature_id !== undefined) {
                // TODO: don't store when in review mode
                $scope.annotation_values[old_feature_id] =
                    $rootScope.imageviewer.grabCurrentTiles().slice(0);
            }
            if (new_feature_id !== undefined) {
                $scope.displayQuestionTiles(new_feature_id);
            }
        });

        $scope.$watch('certaintyModel', function (certaintyModel) {
            if (certaintyModel !== undefined) {
                // label 2 -> 100%
                // label 3 -> 50%
                $rootScope.imageviewer.setActiveState(certaintyModel);
            }
        });

        $scope.$watch('showReview', function (showReview) {
            if (showReview === true) {
                // this will clear the tiles
                $scope.selected_feature_id = null;
            }
        });

        $scope.selectFeature = function (feature_id) {
            $scope.selected_feature_id = feature_id;
        };

        $scope.featureHasPositiveTile = function (feature_id) {
            // TODO: this is being called way too much
            var result;
            var feature_value = $scope.annotation_values[feature_id];
            if (Array.isArray(feature_value)) {
                result = feature_value.some(function (tile_val) {
                    return tile_val !== 0;
                });
            } else {
                result = false;
            }
            return result;
        };

        $scope.displayQuestionTiles = function (feature_id) {
            if (feature_id) {
                $rootScope.imageviewer.displayFeature(feature_id);
            } else {
                $rootScope.imageviewer.clear();
            }
        };
    }
]);

// handle window resize events
function updateLayout() {
    $("#angular_id").height(window.innerHeight);
    $("#annotationView").height(window.innerHeight);
    $("#toolContainer").height(window.innerHeight);

    externalApply();
}

window.onresize = updateLayout;
