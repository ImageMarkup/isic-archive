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

var appController = review_app.controller('ApplicationController', ['$scope', '$rootScope', '$timeout', '$http',
    function ($scope, $rootScope, $timeout, $http) {

        $scope.task_list = [];
        $http.get('/api/v1/uda/task').success(function (data) {
            $scope.task_list = data;
        });

    }]);



