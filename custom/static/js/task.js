'use strict';

var derm_app = angular.module('DermApp');

var REFRESH_INTERVAL = 5000;

derm_app.controller('TaskController', ['$scope', '$http', '$interval',
    function ($scope, $http, $interval) {
        $scope.task_list = [];
        $scope.update = function () {
            $http.get('/api/v1/uda/task').success(function (data) {
                $scope.task_list = data;
            });
        };
        $interval($scope.update, REFRESH_INTERVAL);

        $scope.update();
    }
]);
