/**
 * Created by stonerri on 7/28/14.
 */

'use strict';
/*jslint browser: true*/
/*global console*/

var annotationTool = derm_app.controller('AnnotationTool', ['$scope', '$rootScope', '$timeout', '$sanitize', '$http', '$modal', '$log',
    function ($scope, $rootScope, $timeout, $sanitize, $http, $modal, $log) {

        // single step instance variables

        $scope.step = -1; // current step
        $scope.totalSteps = 0; // total number of steps

        $scope.step_config = undefined; // current step configuration

        $scope.tool_bar_state = undefined; // current toolbar configuration (nested under step)

        $scope.step_options = undefined; // list of options to select (if step has any)


        $scope.formatter = new ol.format.GeoJSON();


        $scope.clearAnnotation = function(){
            $scope.review_mode = false;
            $scope.current_annotation = {
                steps : {}
            };
        };
        $scope.clearAnnotation();

        // annotation instance variables

        $scope.image_index = -1;

        $scope.current_image = $rootScope.active_image;

        // annotation tool parameters

        $scope.draw_mode = 'navigate'; //

        $scope.magicwand_tolerance = 50;

        $scope.regionpaint_size = 70;

        $scope.runningSegmentation = false;

        $rootScope.showingSegmentation = false;


        $rootScope.$watch('user', function(newUser, oldUser){

            if(newUser._id) {


                $scope.loadTasklist();

            }
        });

        $scope.loadTasklist = function () {
            var urlvals = window.location.pathname.split('/');
            var image_item_id = urlvals[urlvals.length - 1];

            var task_detail_url = '/api/v1/uda/task/markup/' + image_item_id;

            $http.get(task_detail_url).success(function (data) {
                $scope.decision_tree = data.decision_tree;
                $scope.phase = data.phase;
                $scope.totalSteps = $scope.decision_tree.length;
                $scope.image_list = data.items;

                $scope.selectImage(0);

                if (data.loadAnnotation) {
                    $scope.current_annotation.steps = data.annotation;
                }

                $scope.nextStep();
            });
        };

        // Accessors

        $scope.getCurrentStepConfig = function () {
            if ($scope.step >= 0) {
                return $scope.decision_tree[$scope.step]
            }
            return undefined;
        };

        $scope.getCurrentAnnotation = function () {
            if ($rootScope.applicationReady) {
                return $scope.current_annotation;
            }
            return undefined;
        };


        // selections
        $scope.selectImage = function (selected_index) {

            $scope.image_index = selected_index;

            $scope.current_image = $scope.image_list[$scope.image_index];

            $rootScope.active_image = $scope.current_image;

            //todo uncomment this eventually

            if ($rootScope.imageviewer) {
                $rootScope.imageviewer.clearPaintByNumber();
            }
        };


        $scope.stepHasDropDownOptions = function () {

            // returns true if current toolbar state is select
            if ($scope.tool_bar_state) {
                return $scope.tool_bar_state === 'select' || $scope.tool_bar_state === 'rppaint';
            }
            return false;

        };


        $scope.canGoToNextStep = function () {

            // returns true if the current step contains the necessary information to go to the next step
//            if ($scope.step == 0){
//
//                // step 0 -> if we have an image
//                return $rootScope.active_image != undefined;
//
//            }
            if ($scope.step === $scope.totalSteps - 1) {
                return true;
            }
            else if ($scope.step >= 0) {
                // step 1=6 -> if we have annotations
                return $scope.stepHasAnnotations($scope.step);
            }

            return false;
        };


        $scope.selectDropDownOption = function(option){

            if (option.type === 'drop'){

                console.log('this is not a valid selection');

            }
            else if (option.type === 'dropchoice') {

                console.log('valid selection, creating annotation and opening modal');

                var feature = new ol.Feature({
                    title: option.title,
                    longtitle: option.longtitle,
                    icon: option.icon,
                    source: 'selectedoption'
                });

                feature.setGeometry(new ol.geom.Point([0, 0]));

                $rootScope.imageviewer.setAnnotations([feature]);

                if(option.options.length > 0) {
                    // contains additional questions in form of modal
                    $scope.openModalWithOptions(option);
                }
            }
            else if (option.type === 'dropoption') {

                console.log('valid paint selection');
                $scope.selectDetail(option);

            }
            else if (option.type === 'gotostep') {

                console.log('valid selection, creating annotation and moving on to next step');

                var feature = new ol.Feature({
                    title: option.title,
                    longtitle: option.longtitle,
                    icon: option.icon,
                    source: 'selectedoption'
                });

                feature.setGeometry(new ol.geom.Point([0, 0]));

                $rootScope.imageviewer.setAnnotations([feature]);

                $scope.gotoStep(option.value);
            }
            else {
                console.log('unhandled option type');
                console.log(option);
            }
        };


        // shortcut key bindings -> takes you home to task list
        Mousetrap.bind( ['ctrl+q'], function (evt) {
            if (typeof (evt.preventDefault) === 'function') {
                evt.preventDefault();
            } else {
                evt.returnValue = false;
            }
            $scope.$apply();
        });

        // shortcut key bindings -> takes you home to task list
        Mousetrap.bind( ['space'], function (evt) {
            if (typeof (evt.preventDefault) === 'function') {
                evt.preventDefault();
            } else {
                evt.returnValue = false;
            }
            $scope.nextStep();

            $scope.$apply();
        });

        Mousetrap.bind( ['ctrl+z'], function (evt) {
            if (typeof (evt.preventDefault) === 'function') {
                evt.preventDefault();
            } else {
                evt.returnValue = false;
            }
            $scope.previousStep();

            $scope.$apply();
        });


        Mousetrap.bind( ['up'], function (evt) {
            if (typeof (evt.preventDefault) === 'function') {
                evt.preventDefault();
            } else {
                evt.returnValue = false;
            }
            $scope.increaseParameter();
            $scope.$apply();
        });


        Mousetrap.bind( ['down'], function (evt) {
            if (typeof (evt.preventDefault) === 'function') {
                evt.preventDefault();
            } else {
                evt.returnValue = false;
            }
            $scope.decreaseParameter();
            $scope.$apply();
        });


        $scope.setDrawMode = function (newDrawMode, newDrawLabel) {
            $scope.draw_mode = newDrawMode;
            $rootScope.imageviewer.setDrawMode(newDrawMode, newDrawLabel);
        };


        // setters
        $scope.saveCurrentStepAnnotation = function () {

            // just making things explicit for readability's sake
            var features = $rootScope.imageviewer.getFeatures();

            console.log('current step features', features);

            var submitTime = Date.now();

            var current_step = $scope.step;

            if (features.length) {

                if ($scope.step_config && $scope.step_config.type) {

                    // if we're in teh superpixel mode, discard the placehold feature and make your own from the external parameters
                    // ugly but it should work.
                    if ($scope.step_config.type === 'superpixel') {

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
                    else if (current_step in Object.keys($scope.current_annotation.steps)) {
                        // we have an existing annotation, just update the features and modify date
//                      var stepAnnotation = currentAnnotation.steps[current_step]

//                      var geojson  = new ol.parser.GeoJSON;
//                      var features = vectorsource.getFeatures();
//                      var json     = geojson.writeFeatures(features);

                        var geojsonfeatures = $scope.formatter.writeFeatures(features);

                        var singleAnnotation = {
                            markup : geojsonfeatures,
                            startTime : $scope.step_start,
                            submitTime : submitTime
                        };

                        $scope.current_annotation.steps[current_step] = singleAnnotation;

                    }
                    else {
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
            else {
                console.log('dont show up here');
            }
            console.log($scope.current_annotation);
        };

//        $scope.saveStepAnnotation = function(annotations, step_to_save){
//
//          var currentAnnotation = $scope.getCurrentAnnotation();
//          currentAnnotation.steps[step_to_save] = annotations;
//        }

        $scope.getStepAnnotations = function () {

//          var currentAnnotation = $scope.getCurrentAnnotation();
            console.log('current annotation', $scope.current_annotation);
            if($scope.current_annotation){
                return $scope.current_annotation.steps[$scope.step]
            }
            return undefined;
        };

        $scope.getAllFeatures = function (returnOlFeatures) {

            var all_features = [];

            for(var step in $scope.current_annotation.steps){
                if (step !== $scope.totalSteps - 1){
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


        $scope.beginAnnotation = function () {
            // clear paint layer if present, then call next step
            if($rootScope.imageviewer){
                $rootScope.imageviewer.clearPaintByNumber();
            }

            $scope.review_mode = false;

            $scope.nextStep();
        };

        $scope.nextStep = function () {
            // if we have the step config, use it to define next step
            if($scope.step_config) {

                if ($scope.step_config.next !== $scope.step) {
                    $scope.gotoStep($scope.step_config.next);
                }
                else {
                    console.log('already at this step');
                }
            }
            else {
                console.log('next', $scope.step+1)
                $scope.gotoStep($scope.step+1);
            }
        };



        $scope.previousStep = function () {
            if($scope.step > 0){
                $scope.gotoStep($scope.step-1);
            }
        };


        $scope.manualEdit = function () {
            $scope.tool_bar_state = 'pldefine';
            $scope.setDrawMode('pointlist', 'lesion');
        };


        $scope.increaseParameter = function () {
            if($scope.tool_bar_state === 'mwdefine'){
                $scope.magicwand_tolerance += 5;
                $scope.imageviewer.setFillParameter($scope.magicwand_tolerance);
                $scope.imageviewer.regenerateFill();
            }
            else if ($scope.tool_bar_state === 'spconfirm'){
                $scope.regionpaint_size += 10;
                $scope.imageviewer.setPaintParameter($scope.regionpaint_size);
                $scope.imageviewer.clearPaintByNumber();

                $scope.runRegionPaintConfigure();
            }
        };

        $scope.decreaseParameter = function () {
            if($scope.tool_bar_state === 'mwdefine') {
                if ($scope.magicwand_tolerance >= 5) {
                    $scope.magicwand_tolerance -= 5;
                }
                else {
                    $scope.magicwand_tolerance = 0;
                }

                $scope.imageviewer.setFillParameter($scope.magicwand_tolerance);
                $scope.imageviewer.regenerateFill();
            }
            else if ($scope.tool_bar_state === 'spconfirm') {

                if ($scope.regionpaint_size >= 10) {
                    $scope.regionpaint_size -= 10;
                }
                else {
                    $scope.regionpaint_size = 0;
                }

                $scope.imageviewer.setPaintParameter($scope.regionpaint_size);
                $scope.imageviewer.clearPaintByNumber();
                $scope.runRegionPaintConfigure();

            }
        };


        // initial function when a step is loaded
        $scope.loadStep = function () {
            // get current step configuration
            $scope.step_config = $scope.getCurrentStepConfig();

            // clear viewer current and temporary annotations
            $scope.clearStep();

            if($scope.step_config && $scope.step_config.type === 'end'){

                $scope.review_mode = true;

                var allFeatures = $scope.getAllFeatures(true);

                if (allFeatures) {

                    $rootScope.imageviewer.setAnnotations(allFeatures);

                }
                else {
                    // this step doesn't have annotations, do appropriate step selection processing steps (aka auto)
                }
            }
            else {

                var stepAnnotation = $scope.getStepAnnotations();

                if (stepAnnotation) {

                    var olFeatures = [];
                    for(var i=0; i < stepAnnotation.markup.features.length; i++){
                        olFeatures.push($scope.formatter.readFeature(stepAnnotation.markup.features[i]))
                    }

                    $rootScope.imageviewer.setAnnotations(olFeatures);
                }
                else {
                }
            }

            // load previous annotations if there are any
//            $rootScope.imageviewer.hidePaintLayerIfVisible();

            $rootScope.showingSegmentation = false;

            if($scope.step_config){

                // set imageviewer to current step configuration
                if ($scope.step_config.default !== "") {

                    if ($scope.step_config.default === 'preloadseg'){

                        var segmentation_url = '/api/v1/item/' + $scope.current_image._id + '/segmentation';

                        $rootScope.showingSegmentation = true;

                        $rootScope.imageviewer.loadPainting(segmentation_url);

                        $scope.setDrawMode('superpixel', $scope.step_config.classification);


                    }
                    else if ($rootScope.imageviewer.hasSegmentation() && $scope.step_config.default === 'superpixel'){

                        $rootScope.showingSegmentation = true;

                        $scope.setDrawMode($scope.step_config.default, $scope.step_config.classification);

                    }
                    else {

                        $scope.setDrawMode($scope.step_config.default, $scope.step_config.classification);
                    }
                }
                else {
                    $scope.setDrawMode('navigate', '');
                }

                if($scope.step_config.zoom === "lesion"){

                    var feature = $scope.getLesionFeature();

                    var olFeature = $scope.formatter.readFeature(feature);

                    $rootScope.imageviewer.moveToFeature(olFeature);

                }

                // set some UI helpers
                $scope.step_options = $scope.step_config.options;
                $scope.step_base = $scope.step_config.step;

                $scope.step_start = Date.now();

                console.log('Finished loading step', $scope.step_config.step, $scope.current_annotation);
            }
        };


        $scope.clearStep = function () {
            // if no annotations, do nothing.
            $scope.clearDrawingTools();

            // if imageviewer annotations, clear them
            $scope.clearLayerAnnotations();

            $scope.select_detail = undefined;
            $scope.select_pattern = undefined;

            // return to original step definition
            if($scope.step_config){
                $scope.tool_bar_state = $scope.step_config.type;
            }
        };


        // returns the first feature from the first lesion definition step
        $scope.getLesionFeature = function () {
            return $scope.current_annotation.steps[0].markup.features[0];
        };

        // this will clear the
        $scope.clearLayerAnnotations = function () {
            $rootScope.imageviewer.clearLayerAnnotations();
        };

        $scope.clearDrawingTools = function () {
            $rootScope.imageviewer.hidePaintLayerIfVisible();
            $rootScope.imageviewer.removeDrawInteraction();
        };


        $scope.gotoStep = function (step) {

            if (step < $scope.totalSteps) {
                // pre step change transition

                // don't save the annotations to review
                if($scope.step === $scope.totalSteps -1 ){

                }
                else {
                    $scope.saveCurrentStepAnnotation();
                }

                $scope.step = step;
                $scope.loadStep();
            }
            else if (step >= $scope.totalSteps) {

                var taskcomplete_time = Date.now();

                var annotation_to_store = {
                    'phase' : $scope.phase,
                    'image' : $scope.current_image,
                    'user' : $rootScope.user,
                    'taskstart' : $rootScope.task_start,
                    'taskend' : taskcomplete_time,
                    'steps' : {}
                };

                for(var k in $scope.current_annotation.steps){
                    annotation_to_store.steps[k] = {
                        markup: $scope.current_annotation.steps[k].markup,
                        startTime: $scope.current_annotation.steps[k].startTime,
                        submitTime: $scope.current_annotation.steps[k].submitTime
                    };
                }

                var task_complete_url = '/api/v1/uda/task/markup/' + $scope.current_image._id + '/complete';

                $http.post(task_complete_url, annotation_to_store).success(function(data){
                    /* // old code to load a new image in-place
                    $scope.step = -1;

                    $scope.step_config = undefined;
                    $scope.review_mode = false;

                    $scope.clearAnnotation();
                    $scope.clearStep();

                    $scope.loadTasklist();

                    // $scope.loadStep();
                    */
                    window.location.replace('/uda/task');
                });
            }
        };


        // Paint by numbers methods

        $scope.runRegionPaint = function () {

            $scope.runningSegmentation = true;

            $timeout(function(){

                $scope.regionPaintDelay();

            }, 50);
        };

        // TODO consider combining independent functions into switched

        $scope.runRegionPaintConfigure = function () {

            $scope.runningSegmentation = true;

            $timeout(function(){

                $scope.regionPaintConfigureDelay();

            }, 50);
        };

        $scope.regionPaintConfigureDelay = function () {

            $scope.tool_bar_state = 'spconfirm';

            var feature = $scope.getLesionFeature();
            var olFeature = $scope.formatter.readFeature(feature);
            $rootScope.imageviewer.moveToFeature(olFeature);

            $scope.setDrawMode('none', '');

            $rootScope.imageviewer.startPainting();

            // this lags for a bit, then returns


            $scope.runningSegmentation = false;

            $rootScope.showingSegmentation = true;
        };


        $scope.regionPaintDelay = function () {

            $scope.tool_bar_state = 'rppaint';

            var feature = $scope.getLesionFeature();
            var olFeature = $scope.formatter.readFeature(feature);
            $rootScope.imageviewer.moveToFeature(olFeature);

            $scope.setDrawMode('paintbrush', '');

            $rootScope.imageviewer.startPainting();

            $scope.runningSegmentation = false;

            $rootScope.showingSegmentation = true;
        };

        $scope.finishRegionPaint = function () {

            $scope.tool_bar_state = 'rpreview';

            $rootScope.imageviewer.acceptPainting();

            $rootScope.showingSegmentation = false;

        };

        $scope.cancelRegionPaint = function () {

            $rootScope.imageviewer.acceptPainting();

            $rootScope.showingSegmentation = false;

            $scope.resetStep();
        };

        $scope.navMode = function () {

            $rootScope.imageviewer.hidePaintLayerIfVisible();

            $rootScope.showingSegmentation = false;

            $scope.setDrawMode('navigate', '');

        };

        $scope.drawMode = function () {

            var feature = $scope.getLesionFeature();
            var olFeature = $scope.formatter.readFeature(feature);
            $rootScope.imageviewer.moveToFeature(olFeature);

            $scope.showingSegmentation = true;

//            $rootScope.imageviewer.showPaintLayerIfVisible();

            $scope.setDrawMode('paintbrush', '');


        };


        // Magic wand methods

        $scope.selectDetail = function (detailobj) {
            $scope.select_detail = detailobj;
            $rootScope.imageviewer.selectAnnotationLabel(detailobj.value);
        };


        var ModalInstanceCtrl = function ($scope, $modalInstance, options) {

            $scope.base = options;
            $scope.selectOption = function(opt){
                $modalInstance.close(opt);
            };
        };



        $scope.openModalWithOptions = function (options) {

            $scope.modal_options = options.options[0];

            var modalInstance = $modal.open({
              templateUrl: 'myModalContent.html',
              controller: ModalInstanceCtrl,
              backdrop: 'static',
              keyboard: false,
              resolve: {
                options: function () {
                  return $scope.modal_options;
                }
              }
            });

            modalInstance.result.then(function (selectedOption) {

                console.log('Selected option', selectedOption);

                // assuming we have steps to go to
                $scope.gotoStep(selectedOption.value);

            }, function () {
              $log.info('Modal dismissed at: ' + new Date());
            });

        };

        $scope.deleteSaved = function (key) {

            if ($rootScope.applicationReady)
            {
                if($scope.current_annotation){
                    if ($scope.current_annotation.steps.hasOwnProperty(key)){
                        delete $scope.current_annotation.steps[key];
                    }
                }

                $scope.clearStep();
            }

            return false;
        };

        // state functions
        $scope.showIfStep = function (step) {
            return parseInt(step) === $scope.step;
        };


        $scope.smartShowHeader = function (step, details) {
            // if the step has annotations, return yes
            if ($scope.stepHasAnnotations(step)) {
                return true;
//                if($scope.review_mode){
//                    return true;
//                }
            }

            if (step === $scope.totalSteps - 1) {
                if ($scope.review_mode) {
                    return true;
                }
            }

            // depending on
            return parseInt(step) === $scope.step;
        };


        $scope.smartShowContent = function (step, details) {
            return parseInt(step) === $scope.step;
        };

        $scope.isLastStep = function () {
            return ($scope.step === ($scope.totalSteps - 1));
        };


        $scope.showIfStepGTE = function (step) {
            return parseInt(step) <= $scope.step;
        };

        $scope.showIfStepOrLast = function (step) {
            if ($scope.step === $rootScope.decision_tree.length - 1) {
                return true;
            }
            return parseInt(step) === $scope.step;
        };

        $scope.compareState = function (target, current_value) {
            return target === current_value;
        };


        // if there are any annotations, you can proceed
        $scope.hasAnnotations = function () {
            return ($scope.hasLayerAnnotations() || $scope.hasStackSelections());
        };

        $scope.imageHasAnnotations = function (index) {

            if ($rootScope.applicationReady)
            {
                if($scope.image_list[index].annotation){
                    return true;
                }
            }
            return false;
        };

        //temporary annotations = points that need to be converted into a polygon
        $scope.hasStackSelections = function () {

            if ($rootScope.applicationReady)
            {
                return $scope.select_stack.length > 0;
            }
            return false;
        };

        // saved annotations = points that have been converted... NOT TO BE CONFUSED WITH STEP annotations
        $scope.hasLayerAnnotations = function () {
            if ($rootScope.applicationReady)
            {
                return $rootScope.imageviewer.hasLayerAnnotations();
            }
            return false;
        };

        $scope.stepHasAnnotations = function (step) {

            if ($rootScope.applicationReady)
            {
                if(step !== $scope.totalSteps -1 ){

                    if ($rootScope.imageviewer.hasLayerAnnotations()){
                        if (step === $scope.step) {
                            return true;
                        }
                    }

                    if ($scope.current_annotation) {

                        var step_annotation = $scope.current_annotation.steps[step];

                        if(step_annotation){
                            return true;
                        }
                    }
                }
            }
            return false;
        };


        $scope.drawModeIs = function (mode_query) {
            if($rootScope.applicationReady) {
                return mode_query === $scope.draw_mode;
            }
            return false;
        };
    }
]);
