'use strict';
/*global $, angular*/
/*jslint browser: true*/

var derm_app = angular.module('DermApp');

// Register 'ol' service
derm_app.value('ol', ol);

// Initialization of angular app controller with necessary scope variables. Inline declaration of external variables
// needed within the controller's scope. State variables (available between controllers using $rootScope). Necessary to
// put these in rootScope to handle pushed data via websocket service.
derm_app.controller('ApplicationController', [
    '$scope', '$rootScope', 'olViewer',
    function ($scope, $rootScope, olViewer) {

        // global ready state variable
        $rootScope.applicationReady = false; // a hack to know when the rest has loaded (since ol3 won't init until dom does)
        $rootScope.imageviewer = undefined; // the ol3 viewer

        // initial layout
        $("#angular_id").height(window.innerHeight);
        $("#map").height(window.innerHeight);

        $rootScope.imageviewer = new olViewer($('#map')[0]);

        // TODO: remove and clean up HTML elements
        $scope.showingSegmentation = false;
    }
]);

derm_app.controller('FlagAnnotationController', [
    '$scope', '$log',
    function ($scope, $log) {
        $scope.flag = function (reason) {
            $scope.abort(reason);
        };
    }
]);

derm_app.controller('SegmentationController', [
    '$scope', '$rootScope', '$location', '$http', '$log', 'Image', 'Segmentation',
    function ($scope, $rootScope, $location, $http, $log, Image, Segmentation) {
        $scope.isSubmitting = false;

        $scope.load = function () {
            var image_id = $location.path().substring(1);

            $scope.image = Image.get({'id': image_id});
            $scope.prev_segmentations = Segmentation.query({'imageId': image_id});
        };
        $scope.load();

        var start_time;
        $scope.$watch('image && image._id', function () {
            if (!$scope.image || !$scope.image.$resolved) {
                return;
            }

            $rootScope.imageviewer.clearCurrentImage();
            $rootScope.imageviewer.loadImageWithURL($scope.image._id);
            $rootScope.imageviewer.clearPaintByNumber();

            start_time = Date.now();
        });

        $scope.canSubmit = function() {
            return Boolean($rootScope.imageviewer.getFeatures().length);
        };

        $scope.doSubmit = function () {
            var formatter = new ol.format.GeoJSON();
            var feature = formatter.writeFeatureObject(
                $rootScope.imageviewer.getFeatures()[0]
            );

            // flip the sign of the y-coordinates
            var coordinates = feature.geometry.coordinates[0];
            for (var j=0; j<coordinates.length; j++) {
                coordinates[j] = $rootScope.imageviewer.flipYCoord(coordinates[j]);
            }
            delete feature.id;
            delete feature.properties.hexcolor;
            delete feature.properties.icon;
            delete feature.properties.rgbcolor;
            delete feature.properties.title;
            feature.properties.startTime = start_time;
            feature.properties.stopTime = Date.now();

            var post_data = {
                imageId: $scope.image._id,
                lesionBoundary: feature
            };
            Segmentation.save({}, post_data, function() {
                $scope.isSubmitting = false;
                window.location.replace('/#tasks');
            });

            $scope.isSubmitting = true;
            // TODO: cause stop() to be called on the active sub-controller,
            //   but without clearing the annotation
            $rootScope.imageviewer.removeDrawInteraction();
            $rootScope.imageviewer.setDrawMode('navigate', 'lesion');
        };
    }
]);

derm_app.controller('SubmitProgressController', [
    '$scope', '$interval',
    function ($scope, $interval) {
        $scope.value = 0.0;
        var interval = 0.2;
        $scope.max = 2.0;

        function increment () {
            $scope.value += interval;
            if ($scope.value === $scope.max) {
                $interval.cancel(promise);
            }
        }

        var promise = $interval(increment, interval * 1000);
    }
]);


derm_app.controller('FloodfillSegmentationController', [
    '$scope', '$rootScope',
    function ($scope, $rootScope) {
        $scope.$parent.$parent.$watch('isOpen', function (isOpen) {
            if (isOpen) {
                start();
            } else {
                stop();
            }
        });

        function start() {
            $rootScope.imageviewer.setDrawMode('autofill', 'lesion');
        }

        function stop() {
            $rootScope.imageviewer.clearLayerAnnotations();
            if ($rootScope.imageviewer.draw_mode === 'autofill') {
                // Directly switching to another accordion opens that one before
                //   this is closed
                $rootScope.imageviewer.setDrawMode('navigate', 'lesion');
            }
        }

        // TODO: The internal tolerance value is not initialized from this
        $scope.magicwand_tolerance = 50;
        function updateParameter () {
            $scope.imageviewer.setFillParameter($scope.magicwand_tolerance);
            $scope.imageviewer.regenerateFill();
        }
        $scope.increaseParameter = function () {
            $scope.magicwand_tolerance += 5;
            updateParameter();
        };
        $scope.decreaseParameter = function () {
            if ($scope.magicwand_tolerance >= 5) {
                $scope.magicwand_tolerance -= 5;
                updateParameter();
            }
        };
    }
]);


derm_app.controller('ManualSegmentationController', [
    '$scope', '$rootScope',
    function ($scope, $rootScope) {
        $scope.$parent.$parent.$watch('isOpen', function (isOpen) {
            if (isOpen) {
                start();
            } else {
                stop();
            }
        });

        function start() {
            $rootScope.imageviewer.setDrawMode('pointlist', 'lesion');
        }

        function stop() {
            $rootScope.imageviewer.clearLayerAnnotations();
            $rootScope.imageviewer.removeDrawInteraction();
            if ($rootScope.imageviewer.draw_mode === 'pointlist') {
                // Directly switching to another accordion opens that one before
                //   this is closed
                $rootScope.imageviewer.setDrawMode('navigate', 'lesion');
            }
        }
    }
]);
