'use strict';

var derm_app = angular.module('DermApp');

var REFRESH_INTERVAL = 60 * 1000;

derm_app.controller('TaskController', ['$scope', '$http', '$interval',
    function ($scope, $http, $interval) {
        $scope.task_list = [];
        $scope.update = function () {
            $http.get('/api/v1/uda/task/qc').success(function (data) {
                $scope.qc_tasks = data;
                $scope.qc_tasks_total = data.reduce(function (total, task_group) {
                    return total + task_group.count;
                }, 0);
            });
            $http.get('/api/v1/task/me/segmentation').success(function (data) {
                $scope.segmentation_tasks = data;
                $scope.segmentation_tasks_total = data.reduce(function (total, task_group) {
                    return total + task_group.count;
                }, 0);
            }).error(function() {
                $scope.segmentation_tasks = [];
                $scope.segmentation_tasks_total = 0;
            });
            $http.get('/api/v1/task/me/annotation').success(function (data) {
                $scope.annotation_tasks = data;
                $scope.annotation_tasks_total = data.reduce(function (total, task_group) {
                    return total + task_group.count;
                }, 0);
            });
        };
        $interval($scope.update, REFRESH_INTERVAL);

        $scope.update();
    }
]);
