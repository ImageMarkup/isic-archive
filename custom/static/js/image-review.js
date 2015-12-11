'use strict';
/*jslint browser: true*/

var isic_app = angular.module('DermApp');

isic_app.controller('ApplicationController',
    ['$scope', '$location', '$http',
    function ($scope, $location, $http) {

        $("#angular_id").height(window.innerHeight - 80 - 100);
        $("#gridcontainer").height(window.innerHeight - 100 - 100);


        var url_path_components = $location.path().substring(1).split('/');
        // TODO: check these params exist
        $scope.gallery_type = url_path_components[0];
        $scope.gallery_id = url_path_components[1];

        var folder_url = '/api/v1/folder/' + $scope.gallery_id;
        var images_url = '/api/v1/item?folderId=' + $scope.gallery_id;
        var taskcomplete_url;
        if ($scope.gallery_type === 'qc') {
            taskcomplete_url = '/api/v1/uda/task/qc/' + $scope.gallery_id + '/complete';
        }

        $scope.sync = function () {
            // get folder details for name and times
            $http.get(folder_url).success(function (data) {
                $scope.folder_details = data;
            });

            // images in folder
            $scope.flagged_list = {};
            $http.get(images_url).success(function (data) {
                $scope.image_list = [];
                data.forEach(function (image) {
                    var simple_rep = image;
                    simple_rep.thumbnail = '/api/v1/image/' + image._id + '/thumbnail?width=512';
                    simple_rep.title = image.name;

                    simple_rep.diagnosis_strings = [];
                    [
                        'diagnosis',
                        //'Diagnosis', // Too long
                        'diagnosis_short',
                        'pathology diagnosis',
                        'pathology diagnosis subtype',
                        'benign_malignant',
                        'ben_mal',
                        'malignant',
                        'Location',
                        'localization'
                    ].forEach(function (key) {
                        var value = image.meta['clinical'][key];
                        if (value) {
                            simple_rep.diagnosis_strings.push(key + ': ' + value);
                        }
                    });

                    $scope.image_list.push(simple_rep);
                });
            });

        };
        $scope.sync();

        $scope.isFlagged = function (index) {
            return $scope.flagged_list.hasOwnProperty(index);
        };

        $scope.toggleFlagged = function (index) {
            var t = $scope.flagged_list[index];

            if (t === undefined) {
                $scope.flagged_list[index] = $scope.image_list[index];
            } else {
                delete $scope.flagged_list[index];
            }
        };

        function submit(include_accepted) {
            var flagged_images = [];
            for (var image_index in $scope.flagged_list) {
                if ($scope.flagged_list.hasOwnProperty(image_index)) {
                    flagged_images.push($scope.flagged_list[image_index]._id);
                }
            }

            var images_to_accept = [];
            if (include_accepted) {
                $scope.image_list.forEach(function (image, image_index) {
                    if (!$scope.flagged_list.hasOwnProperty(image_index)) {
                        images_to_accept.push($scope.image_list[image_index]._id);
                    }
                });
            }

            var payload = {
                flagged: flagged_images,
                good : images_to_accept
            };
            $http.post(taskcomplete_url, payload).success(function() {
                if (include_accepted) {
                    window.location.replace('/uda/task');
                }
                else {
                    // TODO: disable buttons while request is pending
                    $scope.sync();
                }
            });
        }
        $scope.submitAll = function() {
            submit(true);
        };
        $scope.submitFlagged = function() {
            submit(false);
        };

        $scope.hover_image = undefined;

        $scope.mouse = {
            '.' : $scope.nextSet,
            ',' : $scope.previousSet
        };
    }
]);
