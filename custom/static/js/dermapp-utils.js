'use strict';
/*global angular, console*/
/*jslint browser: true*/

// global functions that may be useful

function componentToHex(c) {
    var hex = c.toString(16);
    return hex.length === 1 ? "0" + hex : hex;
}

function rgbToHex(r, g, b) {
    return "#" + componentToHex(r) + componentToHex(g) + componentToHex(b);
}

// handle window resize events
function updateLayout() {
    $("#angular_id").height(window.innerHeight);
    $("#annotationView").height(window.innerHeight);
    $("#toolContainer").height(window.innerHeight);

    var scope = angular.element($("#angular_id")).scope();
    scope.safeApply(function(){
        console.log(window.innerWidth, window.innerHeight);
        //1920 1106
    });
}

function externalApply() {
    var scope = angular.element($("#angular_id")).scope();
    scope.safeApply(function(){
    });
}

window.onresize = updateLayout;
