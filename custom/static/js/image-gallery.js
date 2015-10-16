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


        $("#angular_id").height(window.innerHeight - 80 - 150);
        $("#gridcontainer").height(window.innerHeight - 100 - 150);


//        $scope.parser = document.createElement('a');
//        $scope.url = window.location;

        var api_user_url = '/api/v1/user/me';
        $scope.user = {};
        $http.get(api_user_url).then(function(response){
            console.log(response);
            $scope.user = response.data;
            console.log($scope.user);
        });






        $scope.$watch('user', function(newUser, oldUser){
            if(newUser){
                var urlvals = window.location.pathname.split('/');


                var folder_id = urlvals[urlvals.length - 1];
                console.log(folder_id);

                $scope.images_url = '/api/v1/item?folderId='+folder_id;
                $scope.folder_url = '/api/v1/folder/'+ folder_id;

                $scope.getFolderInfo();
                $scope.getImages();
            }
        });



//        $scope.hover_image = undefined;
//        $scope.flagged_list = {};
//        $scope.image_list = [];

//        $scope.show_flags = false;

//        $scope.download = function(){
//
//            var flags = $scope.flagged_list;
//            flags['user'] = $scope.user_email;
//
//            var json = JSON.stringify(flags);
//            var blob = new Blob([json], {type: "application/json"});
//
//            // save as json to local computer
//            saveAs(blob, "flagged_images.json");
//        };
//

        $scope.getFolderInfo = function(){

            $http.get($scope.folder_url).then(function(response){
                $scope.folder_details = response.data;
                console.log($scope.folder_details);
            })
        }



        $scope.getImages = function(){

            $http.get($scope.images_url).then(function (response) {

                console.log(response);

                var temporary_array = [];

                response.data.forEach(function(image){

                    var simple_rep = image;
                    simple_rep['thumbnail'] = '/api/v1/image/' + image['_id'] + '/thumbnail';
                    simple_rep['image']
                    simple_rep['title'] = image['name'];

                    temporary_array.push(simple_rep);

                });

                $scope.image_list = temporary_array;
                $scope.show_flags = true;

            });
        };


//        $scope.acceptQCandgetNext = function(){
//
////            console.log('will flag images', $scope.flagged_list)
//
//            var images_to_accept = [];
//
//            for(var image_index in $scope.image_list){
//
//                if(image_index in $scope.flagged_list){
////                    console.log(image_index)
//                }
//                else {
//                    images_to_accept.push($scope.image_list[image_index]);
//                }
//            }
//
//            var flagged_images = $scope.flagged_list;
//            var d = Date.now();
//
//            var payload = {
//                flagged : flagged_images,
//                good : images_to_accept,
//                user : $scope.user,
//                date : d
//            };
//
//            $http.post($scope.tasklist_url, payload).then(function(response){
//
//                if(response.status == 200){
//                    console.log('get next list')
//                }
//            });
//        };
//
//
//        $scope.mouse = {
//            '.' : $scope.nextSet,
//            ',' : $scope.previousSet
//        };
//

//        $scope.flagged = function(index){
//            var t = $scope.flagged_list[index];
//            return (t != undefined);
//        };

//        $scope.getOffset = function(index){
//            return $scope.start + index;
//        };
//
//
//        $scope.toggleFlag = function(index){
//
//            var t = $scope.flagged_list[index];
//
//            if (t != undefined) {
//
//                delete $scope.flagged_list[index];
//            }
//            else {
//                $scope.flagged_list[index] = $scope.image_list[index];
//            }
//
//            console.log($scope.flagged_list)
//        };


        $scope.selectImage = function(image){
            $scope.selectedImage = image;
        };


//        $scope.imageHasAnnotations = function(index){
//
//            var res = $scope.image_list[index].annotation > 0;
//            return res;
//        };

        // run me!

//        $scope.getImages();


    }]);



