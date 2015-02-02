/**
 * Created by stonerri on 3/13/14.
 */

'use strict';

// Initialization of angular root application
var review_app = angular.module('DermApp', ['ngSanitize', 'mousetrap']);

review_app.config(function($httpProvider) {
  $httpProvider.defaults.xsrfCookieName = 'girderToken';
  $httpProvider.defaults.xsrfHeaderName = 'Girder-Token';
});

var appController = review_app.controller('TaskController', ['$scope', '$http', '$interval',
    function ($scope, $http, $interval) {

        $scope.task_list = [];
        $scope.update = function () {
            $http.get('/api/v1/uda/task').success(function (data) {
                $scope.task_list = data;
            });
        };
        $interval($scope.update, 5000);

        $scope.update();
    }]);



