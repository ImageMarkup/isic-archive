/**
 * Created by stonerri on 3/13/14.
 */

'use strict';
/*jslint browser: true*/

// Initialization of angular root application
var review_app = angular.module('DermApp', ['ngSanitize', 'mousetrap']);

review_app.config(function ($httpProvider) {
    $httpProvider.defaults.xsrfCookieName = 'girderToken';
    $httpProvider.defaults.xsrfHeaderName = 'Girder-Token';
});

var appController = review_app.controller('ApplicationController', ['$scope', '$rootScope', '$timeout', '$http',
    function ($scope, $rootScope, $timeout, $http) {

        $("#angular_id").height(window.innerHeight - 80 - 100);
        $("#gridcontainer").height(window.innerHeight - 100 - 100);

        var urlvals = window.location.pathname.split('/');
        var folder_id = urlvals[urlvals.length - 1];

        var folder_url = '/api/v1/folder/' + folder_id;
        var images_url = '/api/v1/item?folderId=' + folder_id;
        var taskcomplete_url = '/api/v1/uda/task/qc/' + folder_id + '/complete';

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
                    simple_rep.thumbnail = '/api/v1/image/' + image._id + '/thumbnail?width=256';
                    simple_rep.title = image.name;

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
