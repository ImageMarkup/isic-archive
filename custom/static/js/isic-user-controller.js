'use strict';

var derm_app = angular.module('DermApp');

derm_app.controller('UserController', ['$scope', '$http', '$log',
    function ($scope, $http, $log) {
        var apiUserUrl = '/api/v1/user/me';
        //$scope.user = {};
        $http.get(apiUserUrl).then(function (response) {
            if (response.data) {
                $scope.user = response.data;
            } else {
                $scope.user = {
                    login: 'not logged in',
                    firstName: 'Anonymous',
                    lastName: ''
                };
            }
        });
    }
]);
