/**
 * Created by stonerri on 7/28/14.
 */


var annotationTool = derm_app.controller('AnnotationTool', ['$scope', '$rootScope', '$timeout', '$sanitize', '$http', '$modal', '$log',
    function ($scope, $rootScope, $timeout, $sanitize, $http, $modal, $log) {

        console.log('Initialized annotation tool.');

        $scope.annotation_model = {};
        $scope.annotation_options = undefined;
        $scope.annotation_source = undefined;

        $scope.selected_annotation = undefined;

        $scope.formatter = new ol.format.GeoJSON();

        $rootScope.showingSegmentation = true;

        $rootScope.$watch('user', function(newUser, oldUser){

            if(newUser['_id']){
                $scope.tasklist_url = '/api/v1/user/' + newUser['_id'] + '/tasklist';
                $scope.loadTasklist();
            }
        });

        $scope.loadTasklist = function(){

             $http.get($scope.tasklist_url).then(function(response){


                    $scope.decision_tree = response.data.decision_tree;
                    $scope.phase = response.data.phase;
                    $scope.totalSteps = $scope.decision_tree.length;

                    if(response.data.loadAnnotation){

                        $scope.annotation_source = response.data.annotation;
                        $scope.current_image = response.data.items[0];
                    }

                    $scope.annotation_options = response.data.variables;

                    console.log(response);

                    var segmentation_url = '/api/v1/item/' + $scope.current_image['_id'] + '/segmentation';

                    $rootScope.showingSegmentation = true;

                    $rootScope.imageviewer.loadPainting(segmentation_url);

                })
        };

        $scope.getCurrentAnnotation = function(){

        	if($rootScope.applicationReady){
                return $scope.current_annotation;
        	}
        	return undefined;
        };

        $scope.selectTileAnnotation = function(theTile){

            console.log(theTile);

            $scope.selected_annotation = theTile;

            $rootScope.imageviewer.selectAnnotationLabel('definite');

        };




        // shortcut key bindings -> takes you home to task list
        Mousetrap.bind( ['ctrl+q'], function(evt) {
            if (typeof (evt.preventDefault) === 'function') {evt.preventDefault();}
            else {evt.returnValue = false}
            $scope.$apply();
        });

        // shortcut key bindings -> takes you home to task list
        Mousetrap.bind( ['space'], function(evt) {
            if (typeof (evt.preventDefault) === 'function') {evt.preventDefault();}
            else {evt.returnValue = false}

            $scope.nextStep();
            $scope.$apply();
        });

        Mousetrap.bind( ['ctrl+z'], function(evt) {
            if (typeof (evt.preventDefault) === 'function') {evt.preventDefault();}
            else {evt.returnValue = false}

            $scope.previousStep();
            $scope.$apply();
        });


        Mousetrap.bind( ['up'], function(evt) {
            if (typeof (evt.preventDefault) === 'function') {evt.preventDefault();}
            else {evt.returnValue = false}
            $scope.increaseParameter();
            $scope.$apply();

        });


        Mousetrap.bind( ['down'], function(evt) {
            if (typeof (evt.preventDefault) === 'function') {evt.preventDefault();}
            else {evt.returnValue = false}
            $scope.decreaseParameter();
            $scope.$apply();

        });



        // setters

        $scope.saveCurrentStepAnnotation = function(){

            // just making things explicit for readability's sake
            var features = $rootScope.imageviewer.getFeatures();

            console.log('current step features', features);

            var submitTime = Date.now();

            var current_step = $scope.step;

            if (features.length){

                if ($scope.step_config && $scope.step_config.type){

                    // if we're in teh superpixel mode, discard the placehold feature and make your own from the external parameters
                    // ugly but it should work.
                    if ($scope.step_config.type == 'superpixel'){



                        var segmentationPackage = $rootScope.imageviewer.getSegmentationPackage();

                        var feature = new ol.Feature({
                            title: 'superpixel',
                            longtitle: 'superpixel region',
                            icon: '',
                            source: $scope.phase,
                            parameters: segmentationPackage
                        });

                        // set the geometry of this feature to be the screen extents
                        feature.setGeometry(new ol.geom.Point([0, 0]));

                        var geojsonfeatures = $scope.formatter.writeFeatures([feature]);

                        var singleAnnotation = {
                            markup : geojsonfeatures,
                            startTime : $scope.step_start,
                            submitTime : submitTime
                        };

                        $scope.current_annotation.steps[current_step] = singleAnnotation;
                    }
                    else if(current_step in Object.keys($scope.current_annotation.steps)){

                    // we have an existing annotation, just update the features and modify date
//                    var stepAnnotation = currentAnnotation.steps[current_step]

//                    var geojson  = new ol.parser.GeoJSON;
//                    var features = vectorsource.getFeatures();
//                    var json     = geojson.writeFeatures(features);

                    var geojsonfeatures = $scope.formatter.writeFeatures(features);

                    var singleAnnotation = {
                        markup : geojsonfeatures,
                        startTime : $scope.step_start,
                        submitTime : submitTime
                    };

                    $scope.current_annotation.steps[current_step] = singleAnnotation;

                    }
                    else
                    {
                        // this is the first instance of the annotation, set the create date and field of view as well
                        console.log('this is the first annotation for this step, creating');

                        var geojsonfeatures = $scope.formatter.writeFeatures(features);

                        var singleAnnotation = {
                            markup : geojsonfeatures,
                            startTime : $scope.step_start,
                            submitTime : submitTime
                        };

                        $scope.current_annotation.steps[current_step] = singleAnnotation;
                    }

                }
            }
            else
            {
                console.log('dont show up here');
            }

            console.log($scope.current_annotation);
        };


        $scope.getStepAnnotations = function(){

//        	var currentAnnotation = $scope.getCurrentAnnotation();
        	console.log('current annotation', $scope.current_annotation);
            if($scope.current_annotation){
                return $scope.current_annotation.steps[$scope.step]
            }
            return undefined;
        };

        $scope.getAllFeatures = function(returnOlFeatures){

            var all_features = [];

            for(var step in $scope.current_annotation.steps){
                if (step != $scope.totalSteps - 1){
                    for(var i =0; i < $scope.current_annotation.steps[step].markup.features.length; i++){

                        var feature = $scope.current_annotation.steps[step].markup.features[i];

                        if(returnOlFeatures){

                            // convert feature to ol
                            all_features.push($scope.formatter.readFeature(feature))

                        }
                        else {

                            // push straight geojson features back
                            all_features.push(feature);
                        }
                    }
                }
            }

        	return all_features;
        };


        $scope.nextStep = function(){};

        $scope.previousStep = function(){
            if($scope.step > 0){
                $scope.gotoStep($scope.step-1);
            }
        };


        $scope.increaseParameter = function(){};

        $scope.decreaseParameter = function(){};




    }]);

