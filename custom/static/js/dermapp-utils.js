'use strict';
/*global angular, console*/
/*jslint browser: true*/

// global functions that may be useful

function externalApply() {
    var scope = angular.element($("#angular_id")).scope();
    if (!scope.$root.$$phase) {
        scope.$apply();
    }
}
