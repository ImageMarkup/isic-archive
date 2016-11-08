'use strict';
/*global $, angular, Pixelmap*/

var derm_app = angular.module('DermApp');

// Initialization of angular app controller with necessary scope variables. Inline declaration of external variables
// needed within the controller's scope. State variables (available between controllers using $rootScope). Necessary to
// put these in rootScope to handle pushed data via websocket service.
derm_app.controller('ApplicationController',
    ['$scope', '$rootScope', '$location', '$document',
    function ($scope, $rootScope, $location, $document) {
        // global ready state variable
        $rootScope.applicationReady = false; // a hack to know when the rest has loaded (since ol3 won't init until dom does)
        $rootScope.pixelmap = undefined;

        // main application, gives a bit of a delay before loading everything
        $document.ready(function () {
            $rootScope.pixelmap = new Pixelmap($('#map-container'));
            $rootScope.applicationReady = true;
        });
    }
]);

derm_app.controller('AnnotationController', [
    '$scope', '$rootScope', '$location', '$http',
    'Annotation', 'Study', 'Featureset', 'Image',
    function ($scope, $rootScope, $location, $http,
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

            $rootScope.pixelmap.loadImage(
                $scope.annotation.image._id
            ).done(function () {
                // this callback is being executed from non-Angular code, so we must
                //   wrap all work that it does in an $apply
                $scope.$apply(function () {
                    $scope.clearAnnotations();
                });
            });
            start_time = Date.now();
        });
        $scope.$watch('study && study._id', function () {
            if (!$scope.study || !$scope.study.$resolved) {
                return;
            }
            $scope.featureset = Featureset.get({'id': $scope.study.featureset._id});
        });

        $scope.flagStatus = 'ok';
        $scope.flag = function (newStatus) {
            $scope.flagStatus = newStatus;
        };

        // Submit an annotation task.
        $scope.submitAnnotations = function () {
            var submit_url = '/api/v1/annotation/' + $scope.annotation._id;
            var annotation_to_store = {
                status: $scope.flagStatus,
                imageId: $scope.image._id,
                startTime: start_time,
                stopTime: Date.now(),
                annotations: $scope.annotation_values
            };
            $http.put(submit_url, annotation_to_store).success(function () {
                // window.location.replace('/#tasks');
                // TODO: this won't work if study has no more annotations
                window.location.replace('/api/v1/task/me/annotation/redirect?studyId=' + $scope.study._id);
            });
        };
    }
]);

derm_app.controller('GlobalFeatureAnnotationController', ['$scope',
    function ($scope) {
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
            return selected_option ? selected_option.name : '';
        };

        $scope.selected = function () {
            console.log('selected', $scope.annotation_values);
        };
    }
]);

derm_app.controller('LocalFeatureAnnotationController', ['$scope', '$rootScope',
    function ($scope, $rootScope) {
        $scope.$on('reset', function () {
            // will also be called to initialize
            $scope.certaintyModel = Pixelmap.State.DEFINITE;
            $scope.activeFeatureId = null;
        });

        $scope.$watch('certaintyModel', function (certaintyModel) {
            if (certaintyModel !== undefined) {
                $rootScope.pixelmap.setActiveState(certaintyModel);
            }
        });

        $scope.$watch('showReview', function (showReview) {
            if (showReview === true) {
                $scope.activateFeature(null);
            }
        });

        $scope.anyActive = function () {
            return Boolean($scope.activeFeatureId);
        };

        $scope.isActive = function (featureId) {
            return $scope.activeFeatureId === featureId;
        };

        $scope.onActivateClick = function (featureId) {
            if ($scope.isActive(featureId)) {
                $scope.activateFeature(null);
            } else {
                $scope.activateFeature(featureId);
            }
        };

        $scope.activateFeature = function (featureId) {
            // store the previously active feature
            if ($scope.activeFeatureId) {
                $scope.annotation_values[$scope.activeFeatureId] =
                    $rootScope.pixelmap.getActiveValues();
            }

            $scope.activeFeatureId = featureId;

            if ($scope.activeFeatureId) {
                $rootScope.pixelmap.activate(
                    $scope.annotation_values[$scope.activeFeatureId]);
            } else {
                $rootScope.pixelmap.clear();
            }
        };

        $scope.featureIsSet = function (featureId) {
            return $scope.annotation_values[featureId] !== undefined;
        };

        $scope.deleteFeature = function (featureId) {
            if ($scope.isActive(featureId)) {
                $scope.activateFeature(null);
            }
            delete $scope.annotation_values[featureId];
        };

        $scope.displayFeature = function (featureId) {
            if (featureId) {
                $rootScope.pixelmap.display($scope.annotation_values[featureId]);
            } else {
                $rootScope.pixelmap.clear();
            }
        };
    }
]);
