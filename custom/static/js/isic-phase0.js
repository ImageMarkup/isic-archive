'use strict';

var isic_app = angular.module('DermApp');

isic_app.controller('ApplicationController',
    ['$scope', '$location', '$http',
    function ($scope, $location, $http) {
        $('#angular_id').height(window.innerHeight - 80 - 100);
        $('#gridcontainer').height(window.innerHeight - 100 - 100);

        $scope.sync = function () {
            var url_path_components = $location.path().substring(1).split('/');
            // TODO: check these params exist
            var dataset_id = url_path_components[1];

            // get folder details for name and times
            var dataset_url = '/api/v1/folder/' + dataset_id;
            $http.get(dataset_url).success(function (data) {
                $scope.dataset = data;
            });

            $scope.images = [];
            var images_url = '/api/v1/dataset/' + dataset_id + '/review?limit=50';
            $http.get(images_url).success(function (data) {
                $scope.images = data.map(function (image) {
                    image.thumbnail = '/api/v1/item/' + image._id + '/tiles/region?width=768';

                    image.diagnosis_strings = [];
                    [
                        'benign_malignant',
                        'diagnosis data',
                        'pathology'
                    ].forEach(function (key) {
                        var value = image.meta.clinical[key] || image.meta.unstructured[key];
                        if (value) {
                            image.diagnosis_strings.push(key + ': ' + value);
                        }
                    });

                    image.flagged = false;

                    return image;
                });
            });
        };
        $scope.sync();

        $scope.toggleFlagged = function (image) {
            image.flagged = !image.flagged;
        };

        function submit(include_accepted) {
            var accepted_image_ids = [];
            var flagged_image_ids = [];
            $scope.images.forEach(function (image) {
                if (image.flagged) {
                    flagged_image_ids.push(image._id);
                } else {
                    accepted_image_ids.push(image._id);
                }
            });

            var complete_submit_url = '/api/v1/dataset/' + $scope.dataset._id + '/review';
            var payload = {
                accepted: include_accepted ? accepted_image_ids : [],
                flagged: flagged_image_ids
            };
            $http.post(complete_submit_url, payload).success(function () {
                if (include_accepted) {
                    // var complete_redirect_url = '/#tasks';
                    var complete_redirect_url = '/api/v1/task/me/review/redirect?datasetId=' + $scope.dataset._id;
                    window.location.replace(complete_redirect_url);
                } else {
                    // TODO: disable buttons while request is pending
                    $scope.sync();
                }
            });
        }
        $scope.submitAll = function () {
            submit(true);
        };
        $scope.submitFlagged = function () {
            submit(false);
        };

        $scope.hover_image = undefined;
    }
]);
