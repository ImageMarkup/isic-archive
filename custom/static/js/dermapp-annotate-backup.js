
'use strict';


// what does the annotation metadata look like

//var annotation = {
//    _id : mongo id,
//    user_id : user mongo_id,
//    image_record_id : image record_id,
//    startTime : -1,
//    submitTime : -1,
//    steps : [
//        0 : {
//            features : []
//            selection : []
//            startTime :
//            fieldOfView:
//            endTime :
//        }
//    ]
//}


//var feature = {
//   all the normal geojson
//   classification -> text
//   labelindex -> (optional, needed for paint by number)
//   rgbcolor -> fill color
//   hexcolor -> boundary color
//   source -> magicwand etc
//}



// putting the utilities in the main file
var colorNameToHex = function(colour)
{
    var colours = {"aliceblue":"#f0f8ff","antiquewhite":"#faebd7","aqua":"#00ffff","aquamarine":"#7fffd4","azure":"#f0ffff",
    "beige":"#f5f5dc","bisque":"#ffe4c4","black":"#000000","blanchedalmond":"#ffebcd","blue":"#0000ff","blueviolet":"#8a2be2","brown":"#a52a2a","burlywood":"#deb887",
    "cadetblue":"#5f9ea0","chartreuse":"#7fff00","chocolate":"#d2691e","coral":"#ff7f50","cornflowerblue":"#6495ed","cornsilk":"#fff8dc","crimson":"#dc143c","cyan":"#00ffff",
    "darkblue":"#00008b","darkcyan":"#008b8b","darkgoldenrod":"#b8860b","darkgray":"#a9a9a9","darkgreen":"#006400","darkkhaki":"#bdb76b","darkmagenta":"#8b008b","darkolivegreen":"#556b2f",
    "darkorange":"#ff8c00","darkorchid":"#9932cc","darkred":"#8b0000","darksalmon":"#e9967a","darkseagreen":"#8fbc8f","darkslateblue":"#483d8b","darkslategray":"#2f4f4f","darkturquoise":"#00ced1",
    "darkviolet":"#9400d3","deeppink":"#ff1493","deepskyblue":"#00bfff","dimgray":"#696969","dodgerblue":"#1e90ff",
    "firebrick":"#b22222","floralwhite":"#fffaf0","forestgreen":"#228b22","fuchsia":"#ff00ff",
    "gainsboro":"#dcdcdc","ghostwhite":"#f8f8ff","gold":"#ffd700","goldenrod":"#daa520","gray":"#808080","green":"#008000","greenyellow":"#adff2f",
    "honeydew":"#f0fff0","hotpink":"#ff69b4",
    "indianred ":"#cd5c5c","indigo ":"#4b0082","ivory":"#fffff0","khaki":"#f0e68c",
    "lavender":"#e6e6fa","lavenderblush":"#fff0f5","lawngreen":"#7cfc00","lemonchiffon":"#fffacd","lightblue":"#add8e6","lightcoral":"#f08080","lightcyan":"#e0ffff","lightgoldenrodyellow":"#fafad2",
    "lightgrey":"#d3d3d3","lightgreen":"#90ee90","lightpink":"#ffb6c1","lightsalmon":"#ffa07a","lightseagreen":"#20b2aa","lightskyblue":"#87cefa","lightslategray":"#778899","lightsteelblue":"#b0c4de",
    "lightyellow":"#ffffe0","lime":"#00ff00","limegreen":"#32cd32","linen":"#faf0e6",
    "magenta":"#ff00ff","maroon":"#800000","mediumaquamarine":"#66cdaa","mediumblue":"#0000cd","mediumorchid":"#ba55d3","mediumpurple":"#9370d8","mediumseagreen":"#3cb371","mediumslateblue":"#7b68ee",
    "mediumspringgreen":"#00fa9a","mediumturquoise":"#48d1cc","mediumvioletred":"#c71585","midnightblue":"#191970","mintcream":"#f5fffa","mistyrose":"#ffe4e1","moccasin":"#ffe4b5",
    "navajowhite":"#ffdead","navy":"#000080",
    "oldlace":"#fdf5e6","olive":"#808000","olivedrab":"#6b8e23","orange":"#ffa500","orangered":"#ff4500","orchid":"#da70d6",
    "palegoldenrod":"#eee8aa","palegreen":"#98fb98","paleturquoise":"#afeeee","palevioletred":"#d87093","papayawhip":"#ffefd5","peachpuff":"#ffdab9","peru":"#cd853f","pink":"#ffc0cb","plum":"#dda0dd","powderblue":"#b0e0e6","purple":"#800080",
    "red":"#ff0000","rosybrown":"#bc8f8f","royalblue":"#4169e1",
    "saddlebrown":"#8b4513","salmon":"#fa8072","sandybrown":"#f4a460","seagreen":"#2e8b57","seashell":"#fff5ee","sienna":"#a0522d","silver":"#c0c0c0","skyblue":"#87ceeb","slateblue":"#6a5acd","slategray":"#708090","snow":"#fffafa","springgreen":"#00ff7f","steelblue":"#4682b4",
    "tan":"#d2b48c","teal":"#008080","thistle":"#d8bfd8","tomato":"#ff6347","turquoise":"#40e0d0",
    "violet":"#ee82ee",
    "wheat":"#f5deb3","white":"#ffffff","whitesmoke":"#f5f5f5",
    "yellow":"#ffff00","yellowgreen":"#9acd32"};

    if (typeof colours[colour.toLowerCase()] != 'undefined')
        return colours[colour.toLowerCase()];

    return false;
}

function componentToHex(c) {
    var hex = c.toString(16);
    return hex.length == 1 ? "0" + hex : hex;
}

function rgbToHex(r, g, b) {
    return "#" + componentToHex(r) + componentToHex(g) + componentToHex(b);
}

var _labels = [
    { name: 'background', color: [255, 255, 255]},
    { name: 'foreground', color: [255, 255, 255]},
    { name : '10', color: [251, 17, 13], icon: "static/derm/images/5-lines.jpg", title: 'Lines' },
    { name : '20', color: [251, 18, 13], icon: "static/derm/images/5-lines_reticular.jpg", title: 'Reticular' },
    { name : '21', color: [251, 19, 13], icon: "static/derm/images/5-lines_reticular_regular.jpg", title: 'Regular' },
    { name : '22', color: [251, 20, 13], icon: "static/derm/images/5-lines_reticular_thick.jpg", title: 'Thick' },
    { name : '23', color: [251, 21, 13], icon: "static/derm/images/5-lines_reticular_thin.jpg", title: 'Thin' },
    { name : '24', color: [251, 22, 13], icon: "static/derm/images/5-lines_reticular_atypical.jpg", title: 'Atypical' },
    { name : '25', color: [251, 23, 13], icon: "static/derm/images/5-lines_reticular_negativenetwork.jpg", title: 'Negative Network' },
    { name : '30', color: [251, 24, 13], icon: "static/derm/images/5-lines_radial.jpg", title: 'Radial' },
    { name : '31', color: [251, 25, 13], icon: "static/derm/images/5-lines_radial_radiallinesconnectedtoacommonbase.jpg", title: 'Radial lines connected to a common base' },
    { name : '32', color: [251, 26, 13], icon: "static/derm/images/5-lines_radial_radiallinesconvergingtoacentraldot.jpg", title: 'Radial lines converging to a central dot' },
    { name : '33', color: [251, 27, 13], icon: "static/derm/images/5-lines_radial_radiallines-peripheral.jpg", title: 'Radial lines, peripheral' },
    { name : '40', color: [251, 28, 13], icon: "static/derm/images/5-lines_branched.jpg", title: 'Branched' },
    { name : '50', color: [251, 29, 13], icon: "static/derm/images/5-lines_parallelandstraight.jpg", title: 'Parallel and straight' },
    { name : '51', color: [251, 30, 13], icon: "static/derm/images/5-lines_parallelandstraight_furrows.jpg", title: 'Furrows' },
    { name : '52', color: [251, 31, 13], icon: "static/derm/images/5-lines_parallelandstraight_ridges.jpg", title: 'Ridges' },
    { name : '53', color: [251, 32, 13], icon: "static/derm/images/5-lines_parallelandstraight_fibrallar.jpg", title: 'Fibrallar' },
    { name : '60', color: [251, 33, 13], icon: "static/derm/images/5-lines_curved.jpg", title: 'Curved' },
    { name : '61', color: [251, 34, 13], icon: "static/derm/images/5-lines_curved_thick.jpg", title: 'Thick' },
    { name : '62', color: [251, 35, 13], icon: "static/derm/images/5-lines_curved_thin.jpg", title: 'Thin' },
    { name : '41', color: [251, 36, 13], icon: "static/derm/images/5-lines_zigzag.jpg", title: 'Zig Zag' },
    { name : '70', color: [236, 252, 37], icon: "static/derm/images/5-dots-clods.jpg", title: 'Dots & Clods' },
    { name : '71', color: [236, 252, 38], icon: "static/derm/images/5-dots-clods_dots.jpg", title: 'Dots' },
    { name : '72', color: [236, 252, 39], icon: "static/derm/images/5-dots-clods_dots_atypicaldots.jpg", title: 'Atypical Dots' },
    { name : '73', color: [236, 252, 40], icon: "static/derm/images/5-dots-clods_dots_dots-foursquare.jpg", title: 'Dots, Four square' },
    { name : '74', color: [236, 252, 41], icon: "static/derm/images/5-dots-clods_dots_dots-circle.jpg", title: 'Dots, Circle' },
    { name : '75', color: [236, 252, 42], icon: "static/derm/images/5-dots-clods_dots_dots-lines.jpg", title: 'Dots, Lines' },
    { name : '76', color: [236, 252, 43], icon: "static/derm/images/5-dots-clods_clods.jpg", title: 'Clods' },
    { name : '77', color: [236, 252, 44], icon: "static/derm/images/5-dots-clods_clods_atypicalclods.jpg", title: 'Atypical Clods' },
    { name : '80', color: [126, 45, 169], icon: "static/derm/images/5-structureless.jpg", title: 'Structureless' },
    { name : '81', color: [126, 46, 169], icon: "static/derm/images/5-structureless_blue-whiteveil.jpg", title: 'Blue-White Veil' },
    { name : '82', color: [126, 47, 169], icon: "static/derm/images/5-structureless_pseudonetwork.jpg", title: 'Pseudonetwork' },
    { name : '83', color: [126, 48, 169], icon: "static/derm/images/5-structureless_peripheralbrownstructurelessarea.jpg", title: 'Peripheral brown structureless area' },
    { name : '84', color: [126, 49, 169], icon: "static/derm/images/5-structureless_off-centeredblotch.jpg", title: 'Off-centered blotch' },
    { name : '100', color: [20, 209, 50], icon: "static/derm/images/5-vessels.jpg", title: 'Vessels' },
    { name : '110', color: [20, 209, 51], icon: "static/derm/images/5-vessels_lines.jpg", title: 'Lines' },
    { name : '111', color: [20, 209, 52], icon: "static/derm/images/5-vessels_lines_straight.jpg", title: 'Straight' },
    { name : '112', color: [20, 209, 53], icon: "static/derm/images/5-vessels_lines_looped.jpg", title: 'Looped' },
    { name : '113', color: [20, 209, 54], icon: "static/derm/images/5-vessels_lines_looped_loopedwithwhitehalo.jpg", title: 'Looped with white Halo' },
    { name : '114', color: [20, 209, 55], icon: "static/derm/images/5-vessels_lines_curved.jpg", title: 'Curved' },
    { name : '115', color: [20, 209, 56], icon: "static/derm/images/5-vessels_lines_serpentine.jpg", title: 'Serpentine' },
    { name : '116', color: [20, 209, 57], icon: "static/derm/images/5-vessels_lines_helical.jpg", title: 'Helical' },
    { name : '117', color: [20, 209, 58], icon: "static/derm/images/5-vessels_lines_coiled.jpg", title: 'Coiled' },
    { name : '118', color: [20, 209, 59], icon: "static/derm/images/5-vessels_lines_branched.jpg", title: 'Branched' },
    { name : '101', color: [20, 209, 60], icon: "static/derm/images/5-vessels_dots.jpg", title: 'Dots' },
    { name : '102', color: [20, 209, 61], icon: "static/derm/images/5-vessels_clods.jpg", title: 'Clods' },
    { name : '120', color: [20, 209, 62], icon: "static/derm/images/5-vessels_milky-redarea.jpg", title: 'Milky-red area' },
    { name : '130', color: [20, 209, 63], icon: "static/derm/images/5-vessels_polymorphousvessels.jpg", title: 'Polymorphous vessels' },
    { name : '140', color: [64, 140, 255], icon: "static/derm/images/5-other.jpg", title: 'Other' },
    { name : '150', color: [65, 140, 255], icon: "static/derm/images/5-other_shinywhitelines.jpg", title: 'Shiny white lines' },
    { name : '151', color: [66, 140, 255], icon: "static/derm/images/5-other_circles.jpg", title: 'Circles' },
    { name : '152', color: [67, 140, 255], icon: "static/derm/images/5-other_pseudopods.jpg", title: 'Pseudopods' },
    { name : '153', color: [68, 140, 255], icon: "static/derm/images/5-other_sharplydemarcatedscallopedborder.jpg", title: 'Sharply demarcated scalloped border' }
];





// Initialization of angular root application
var derm_app = angular.module('DermApp', ['ui.bootstrap', 'ngSanitize', 'xml']);

derm_app.value( "ol", ol );

var olViewer = derm_app.factory('olViewer', function(ol, $http, xmlParser) {

        var olViewer = function(viewer_options) {

//            console.log('Creating OLViewer with opts', viewer_options, this);

            var self = this;

            // Instance variables
            this.image_source = undefined;
            this.image_layer = undefined;

            this.map = undefined;
            this.draw_mode = undefined;
            this.draw_label = undefined;

            this.last_click_location = undefined;
            this.last_job_id = undefined;
            this.fill_tolerance = 50;

            this.paint_size = 70;

//            this.select_interaction = new ol.interaction.Select();
//            this.selected_features = this.select_interaction.getFeatures();
//            var collection = select.getFeatures();
//            this.selected_features.on('add', function(e){
//                console.log('add', e)
//            });
//            this.selected_features.on('remove', function(e){
//                console.log('remove', e)
//            });

            // annotations added that need to be saved
//            this.clearTemporaryAnnotations();

            // current list of features
            // annotations previously saved

            var styleFunction = (function() {

                 return function(feature, resolution) {


                      if(feature.get('hexcolor')){
                         return [new ol.style.Style({
                        stroke: new ol.style.Stroke({
                          color: feature.get('hexcolor'),
                          width: 2
                        }),
                        fill: new ol.style.Fill({
                            color: feature.get('rgbcolor')
                        })
                      })]
                      }
                     else
                      {
                         return [new ol.style.Style({
                            fill: new ol.style.Fill({
                              color: 'rgba(255, 255, 255, 0.2)'
                            }),
                            stroke: new ol.style.Stroke({
                              color: '#000000',
                              width: 0
                            }),
                            image: new ol.style.Circle({
                              radius: 0,
                              fill: new ol.style.Fill({
                                color: '#000000'
                              })
                            })
                          })]
                      }


                  };
            })();

            this.vector_source = new ol.source.Vector();
            this.vector_layer = new ol.layer.Vector({
                source: this.vector_source,
                style: styleFunction
            })

            this.draw_interaction = new ol.interaction.Draw({
                source: this.vector_source,
                type: 'Polygon'
            })

            this.draw_interaction.on('drawend', function(e){

                var properties = {};

                if(self.draw_label == 'lesion'){

                    properties['icon'] = "static/derm/images/lesion.jpg";
                    properties['hexcolor'] = '#ff0000';
                    properties['source'] = 'manual pointlist';
                    properties['title'] = self.draw_label;
                    properties['rgbcolor'] = 'rgba(255, 255, 255, 0.1)';

                }
                else if (self.draw_label == 'normal') {

                    properties['icon'] = "static/derm/images/normal.jpg";
                    properties['hexcolor'] = '#0099ff';
                    properties['source'] = 'manual pointlist';
                    properties['title'] = self.draw_label;
                    properties['rgbcolor'] = 'rgba(255, 255, 255, 0.1)';

                }

                e.feature.setValues(properties);

//                console.log(e.feature.getProperties())
                // need to manually update the angular state, since they're not directly linked
                externalApply();
            });

            // initialize map (imageviewer)
            this.map = new ol.Map({
                renderer:'canvas',
                target: 'map'
            });


            
            
            // set map event handlers
            this.map.on('singleclick', function(evt) {

                var click_coords = [evt.coordinate[0], -evt.coordinate[1]];

                if (self.draw_mode == 'navigate') {

                    self.last_click_location = click_coords;

//                    featuresAtPoint(pixel);

                } else if (self.draw_mode == 'pointlist') {

                    self.last_click_location = evt.coordinate;

//                    self.addPoint(evt.coordinate);

                } else if (self.draw_mode == 'autofill') {

                    self.last_click_location = click_coords;

                   	self.autofill(click_coords)

                } else if (self.draw_mode == 'lines') {

                    self.last_click_location = evt.coordinate;
                    self.addPoint(evt.coordinate);
                } 
            });

            $(this.map.getViewport()).on('mousemove', function(evt) {
              var pixel = self.map.getEventPixel(evt.originalEvent);
              self.featuresAtPoint(pixel);
            });

        }


        // Define the "instance" methods using the prototype
        // and standard prototypal inheritance.
        olViewer.prototype = {

            clearCurrentImage : function(){

                if(this.image_layer){
                    this.map.removeLayer(this.image_layer);
                }

            },


            hasLayerAnnotations : function() {
                return this.vector_source.getFeatures().length > 0;
            },

            moveToFeature: function(feature){
                var featuresExtent = ol.extent.createEmpty();
                ol.extent.extend(featuresExtent, feature.getGeometry().getExtent());
                this.map.getView().fitExtent(featuresExtent, this.map.getSize());
            },

            featuresAtPoint: function(pixel){

//                console.log(pixel);

                  var feature = this.map.forEachFeatureAtPixel(pixel, function(feature, layer) {
                    return feature;
                  });
                  var info = document.getElementById('objectinfo');

                  if (feature) {

                      var icon = feature.get('icon');

                      if(icon){
                        info.src = icon;
                        info.style.display = 'inline';
                      }
                      else {
                        info.src = 'static/na.jpg'
                        info.style.display = 'none';
                      }
                  }
                  else {
                      info.style.display = 'none';
                      info.src = 'static/na.jpg'
                  }
            },


            featureListFromAnnotation : function(annotation){

            	// console.log(annotation);
                var features_list = [];

                if (annotation.polygons.length > 0) {

                    var af_feature = new ol.Feature({
                        'classification' : annotation.classification
                    });

                    af_feature.setGeometry(new ol.geom.Polygon([annotation.polygons]))
                    features_list.push(af_feature)
                }

				if (annotation.lines.length > 0) {

                    var l_feature = new ol.Feature({
                        'classification' : annotation.classification
                    });

                    l_feature.setGeometry(new ol.geom.Polygon([annotation.lines]))
                    features_list.push(l_feature)
                }

                return features_list;

            },

            getFeatures : function(){
                return this.vector_source.getFeatures();
            },

            setAnnotations : function(features){
            	if (features) {
                    this.vector_source.addFeatures(features);
            	}
            },

//            clearTemporaryAnnotations : function(){
//
//                // temporary annotations are created
//				this.temporary_annotations = {
//                    features : [],
//	                polygons : []
//	            };
//            },

            clearLayerAnnotations : function(step){
                this.vector_source.clear();
            },

            acceptPainting : function(){

                var annotation = this.segmentannotator.getAnnotation();
                var extent = this.map.getView().calculateExtent(this.map.getSize());
                var tr = ol.extent.getTopRight(extent);
                var bl = ol.extent.getBottomLeft(extent);
                var segmenturl = 'segment'

                var msg = {};
                msg['image'] = annotation
                msg['extent'] = [tr, bl]

                var self = this;
                // interesting hack to get the UI to update without external scopy applys
                $http.post(segmenturl, msg).success(function(response){

                    console.log(response);

                    self.vector_source.clear();

                    var f = new ol.format.GeoJSON()

                    for(var i=0;i<response.features.length;i++){

                        var jsObject = JSON.parse(response.features[i])

                        var label = _labels[parseInt(jsObject['properties']['labelindex'])]
                        jsObject['properties']['label'] = label

                        var hexcolor = rgbToHex(label['color'][0], label['color'][1], label['color'][2])
                        var rgbcolor = 'rgba(' + label['color'][0] + ',' + label['color'][1] + ',' + label['color'][2] + ',0.0)';

                        jsObject['properties']['rgbcolor'] = rgbcolor;
                        jsObject['properties']['icon'] = label.icon;
                        jsObject['properties']['hexcolor'] = hexcolor;
                        jsObject['properties']['title'] = label.title;

                        var featobj = f.readFeature(jsObject);

//                        console.log(featobj)
//                        console.log(featobj.getProperties())

                        self.vector_source.addFeature(featobj)

                    }

                    $("#annotatorcontainer").hide();
//                    self.segmentannotator.container.hidden = true;

                    // manually request an updated frame async
                    self.map.render()

                });
            },

            selectAnnotationLabel : function(detailvalue){

                this.segmentannotator.setCurrentLabel(detailvalue.toString());

            },

            hidePaintLayerIfVisible : function(){

                if(this.segmentannotator){

                    $("#annotatorcontainer").hide();
                }
            },

            showPaintLayerIfVisible : function(){

                if(this.segmentannotator){

                    $("#annotatorcontainer").show();
                    this.map.render();
                    return true;
                }
                return false;
            },

            removeDrawInteraction : function(){

                if(this.draw_interaction){
                    this.map.removeInteraction(this.draw_interaction);
                }
            },


            clearPaintByNumber : function(){

                if(this.segmentannotator){

                    delete this.segmentannotator;
                    $('#annotatorcontainer').empty();
                }
            },

            startPainting : function(){

                var self = this;

                this.map.once('postcompose', function(event) {

                    var canvas = event.context.canvas;

                    if(self.segmentannotator){

                        self.showPaintLayerIfVisible()
                    }
                    else {

//                        console.log("input", canvas.width, canvas.height);

                        self.segmentannotator = new SLICSegmentAnnotator(canvas, {
                            regionSize: self.paint_size,
                            container: document.getElementById('annotatorcontainer'),
                            backgroundColor: [0,0,0],
                            fillAlpha: 0,
                            highlightAlpha: 0,
                            boundaryAlpha: 190,
                            labels: _labels,
                            onload: function() {
                                $("#annotatorcontainer").show();
                            }
                          });

                    }

                    self.segmentannotator.setCurrentLabel(0);

                });
            },

            setFillParameter : function(new_fill_tolerance){
                this.fill_tolerance = new_fill_tolerance;
            },

            setPaintParameter : function(new_paint_size){
                this.paint_size = new_paint_size;
            },

            regenerateFill : function(){

              this.autofill(this.last_click_location);

            },



            autofill : function(click_coords){

                var self = this;

                var extent = this.map.getView().calculateExtent(this.map.getSize());
                var tr = ol.extent.getTopRight(extent)
                var tl = ol.extent.getTopLeft(extent)
                var bl = ol.extent.getBottomLeft(extent)

                // think: if x is positive on left, subtract from total width
                // if x on right is greater than width, x = width

                var origin_x = 0;
                var origin_y = 0;

                var click_x_offset = 0;
                var click_y_offset = 0;

                var newWidth = this.nativeSize.w;

                if(tr[0] < this.nativeSize.w) {
                    newWidth = tr[0];
                };
                if(tl[0] > 0) {
                    newWidth -= tl[0]
                    origin_x = tl[0]
                };

                var newHeight = this.nativeSize.h;
                
                if(- bl[1] < this.nativeSize.h) {
                    newHeight = -bl[1];
                };
                if(tl[1] < 0) {
                    newHeight += tl[1];
                    origin_y = -tl[1];
                }                

                console.log(origin_x, origin_y, newWidth, newHeight);

                if (newWidth <= 0 || newHeight <= 0){
                    console.log('offscreen or invalid region');
                };

                var rel = []
                rel[0] = origin_x / this.nativeSize.w;
                rel[1] = origin_y / this.nativeSize.h;
                rel[2] = newWidth / this.nativeSize.w;
                rel[3] = newHeight / this.nativeSize.h;

                var dataurl = function(rel, width){
                    return '/&WID=' + width + '&RGN=' + rel.join(',') + '&CVT=jpeg'
                };

                // var url_to_use = this.data_url + '&WID=400&RGN=0.25,0.25,0.5,0.5&CVT=jpeg'
                var url_to_use = this.data_url + dataurl(rel, 500);

                var subimage = {};
                subimage.origin = [origin_x, origin_y];
                subimage.size = [newWidth, newHeight];
                subimage.rel = rel;
                var origimage = {};
                origimage.origin = [0,0];
                origimage.size = [this.nativeSize.w, this.nativeSize.h];


                // relative click is not based on the image origin, but rather the extent origin
                var click = {};
                click.absolute = click_coords;
                click.relative = [(click_coords[0])/this.nativeSize.w, (click_coords[1])/this.nativeSize.h]


                var msg = {};
                msg.image = {};
                msg.image.region = subimage;
                msg.image.base = origimage;
                msg.image.url = url_to_use;
                msg.tolerance = this.fill_tolerance;
                msg.click = click;

                // console.log(msg);

                var segmentURL = 'fill';

                $http.post(segmentURL, msg).success(function(response){

                    self.vector_source.clear();
                    var f = new ol.format.GeoJSON();

                    for(var i=0;i<response.features.length;i++){

                        var jsObject = response.features[i]
                        var featobj = f.readFeature(jsObject);

                        var iconpath = "static/derm/images/lesion.jpg";

                        featobj.setValues({
                            'title' : self.draw_label,
                            'icon' : iconpath
                        });

                        self.vector_source.addFeature(featobj)

                    }

                    // manually request an updated frame async
                    self.map.render()

                });

            },

            hasJobResult : function(results){

                if(results.uuid == this.last_job_id){

                    console.log(results.result);
                }

            },

            setDrawMode : function(draw_mode, draw_label) {

                this.draw_mode = draw_mode;
                this.draw_label = draw_label;

                console.log('Draw settings:', this.draw_mode, this.draw_label);

                if (draw_mode == 'navigate') {
                } else if (draw_mode == 'paintbrush') {
                } else if (draw_mode == 'autofill') {
                } else if (draw_mode == 'pointlist') {

                    this.map.addInteraction(this.draw_interaction)

                }

            },



            getSegmentationPackage : function(){

                var extent = this.map.getView().calculateExtent(this.map.getSize());
                var tr = ol.extent.getTopRight(extent);
//                var tl = ol.extent.getTopLeft(extent)
                var bl = ol.extent.getBottomLeft(extent);

                var content = {
                    'topright' : ol.extent.getTopRight(extent),
                    'topleft' : ol.extent.getTopLeft(extent),
                    'bottomright' : ol.extent.getBottomRight(extent),
                    'bottomleft' : ol.extent.getBottomLeft(extent),

                }


                return this.segmentannotator.getAllData();
            },

//          designed for the Girder-based url-rewrite.
            loadImageWithURL : function(base_url) {

                var self = this;
                self.segmentation_list = [];

                self.zoomify_url = base_url + '/zoomify';
                self.data_url = 'http://localhost' +  base_url + '/fif';

                var image_properties_xml = self.zoomify_url  + '/ImageProperties.xml';

                $http.get(image_properties_xml).then(function (hresp) {

                    /* Parse a Zoomify protocol metadata request
                    */
                    var parseMetaData = function(response){
                        // Simply split the reponse as a string
                        var tmp = response.split('"');
                        var w = parseInt(tmp[1]);
                        var h = parseInt(tmp[3]);
                        var ts = parseInt(tmp[11]);
                        // Calculate the number of resolutions - smallest fits into a tile
                        var max = (w>h)? w : h;
                        var n = 1;
                        while( max > ts ){
                          max = Math.floor( max/2 );
                          n++;
                        }
                        var result = {
                          'max_size': { w: w, h: h },
                          'tileSize': { w: ts, h: ts },
                          'num_resolutions': n
                        };
                        return result;
                    }

                    var metadata = parseMetaData(hresp.data)
                    // console.log(metadata);

                    self.imageCenter = [metadata.max_size.w / 2, - metadata.max_size.h / 2];

                    self.proj = new ol.proj.Projection({
                        code: 'ZOOMIFY',
                        units: 'pixels',
                        extent: [0, 0, metadata.max_size.w, metadata.max_size.h]
                    });

                    var crossOrigin = 'anonymous';

                    self.image_source = new ol.source.Zoomify({
                        url: self.zoomify_url + '/',
                        size: [metadata.max_size.w, metadata.max_size.h],
                        crossOrigin: crossOrigin,
                    });

                    self.image_layer = new ol.layer.Tile({
                       source: self.image_source,
                       preload: 1
                    })

                    self.nativeSize = metadata.max_size;

                    self.view = new ol.View2D({
                      projection: self.proj,
                      center: self.imageCenter,
                      zoom: 2,
                      maxZoom: metadata.num_resolutions
                    })

                    self.map.addLayer(self.image_layer);
                    self.map.addLayer(self.vector_layer);
                    self.map.setView(self.view);
                })
            }
        };

        return( olViewer );

        }
    );
    












































// Initialization of angular app controller with necessary scope variables. Inline declaration of external variables
// needed within the controller's scope. State variables (available between controllers using $rootScope). Necessary to
// put these in rootScope to handle pushed data via websocket service.
var appController = derm_app.controller('ApplicationController', ['$scope', '$rootScope', '$location', '$timeout', '$http', 'olViewer',
    function ($scope, $rootScope, $location, $timeout, $http, olViewer) {

        // global ready state variable
        $rootScope.applicationReady = false; // a hack to know when the rest has loaded (since ol3 won't init until dom does)

        $rootScope.imageviewer = undefined; // the ol3 viewer

        $scope.active_image = undefined; // image metedata for currently viewed image

         // pull user variables (via template render) in js app...
         var current_user = $("#user_email").val();
         var current_user_id = $("#user_id").val();

        var api_user_url = '/api/v1/user/me';
        $rootScope.user = {};
        $http.get(api_user_url).then(function(response){
            $rootScope.user = response.data;

            $rootScope.user_email = $scope.user['email'];
            $rootScope.user_id = $scope.user['_id'];
        });


        // initial layout
        $("#angular_id").height(window.innerHeight);
        $("#map").height(window.innerHeight);

        $timeout(function(){
            $rootScope.ApplicationInit();
        }, 10);


        // main application, gives a bit of a delay before loading everything
        $rootScope.ApplicationInit = function() {

            $rootScope.debug  = $location.url().indexOf('debug') > -1;
            $rootScope.imageviewer = new olViewer({'div' : 'annotationView'});
            $rootScope.applicationReady = true;

        };


        $rootScope.$watch('active_image', function(newImage, oldValue){

            if ($rootScope.applicationReady){

                $rootScope.imageviewer.clearCurrentImage();

                var image_url = '/api/v1/item/' + newImage['_id'];

                $rootScope.imageviewer.loadImageWithURL(image_url);

            }
        })

        $scope.safeApply = function( fn ) {
            var phase = this.$root.$$phase;
            if(phase == '$apply' || phase == '$digest') {
                if(fn) { fn(); }
            } else {
                this.$apply(fn);
            }
        };

}]);













































var annotationTool = derm_app.controller('AnnotationTool', ['$scope', '$rootScope', '$timeout', '$sanitize', '$http', '$modal', '$log', 'decisionTree', 'imageList',
    function ($scope, $rootScope, $timeout, $sanitize, $http, $modal, $log, decisionTree, imageList ) {

        console.log('Initialized annotation tool.');

        // single step instance variables

        $scope.step = -1; // current step
        $scope.totalSteps = 0; // total number of steps

        $scope.step_config = undefined; // current step configuration

        $scope.tool_bar_state = undefined; // current toolbar configuration (nested under step)

        $scope.step_options = undefined; // list of options to select (if step has any)

        $scope.select_detail = undefined;
        $scope.select_pattern = undefined;

        $scope.review_mode = false;


        // session instance variables

        $scope.completedImages = 0; // number of images that have annotations in current set

        $scope.totalItems = 0; // total number of items in the set






        $scope.annotations = undefined; // the annotation metadata for all images in the current set








        // annotation instance variables

        $scope.image_index = -1;
        $scope.current_image = $rootScope.active_image;

        // annotation tool parameters

        $scope.draw_mode = 'navigate'; //
        $scope.magicwand_tolerance = 50;
        $scope.regionpaint_size = 70;
        $scope.runningSegmentation = false;




        $rootScope.$watch('user', function(newUser, oldUser){

            if(newUser['_id']){

                console.log(newUser);

                $scope.tasklist_url = '/api/v1/user/' + newUser['_id'] + '/tasklist';

                $http.get($scope.tasklist_url).then(function(response){

                    console.log(response);

                    $scope.decision_tree = response.data.decision_tree;
                    $scope.phase = response.data.phase;
                    $scope.totalSteps = $scope.decision_tree.length;
                    $scope.image_list = response.data.items;

                    $scope.annotations = [];
                    $.each($scope.image_list, function(n, image_data){
                         var placeholder_obj = {
                             annotationid: -1,
                             steps: {}
                         };
                         $scope.annotations.push(placeholder_obj);
                     });

                    $scope.nextStep();



                    $scope.selectImage(0);

                })
            }
        });




        // initial instance methods

        $scope.loadDecisionTree = function(){

//             console.log('Loading decisiontree');

             decisionTree.fromLocal().then(function(d){

//                 console.log(d);
                $scope.decision_tree = d;
             });
        }




        // effectively a callback from the initial subject query
//        $scope.$watch('decision_tree', function(newValue, originalValue) {
//
//            if(newValue){
//
//                console.log("There are " + $scope.decision_tree.length + ' steps');
//
//                $scope.totalSteps = $scope.decision_tree.length;
//
//                var useRandom = $scope.decision_tree[0].random;
//                var imageCount = $scope.decision_tree[0].count;
//                var startingIndex = 0;
//
//                if(useRandom){
//                    startingIndex =  Math.floor(190 * Math.random());
//                }
//
//                imageList.fromDB($rootScope.user_email, startingIndex, imageCount, false).then(function(d){
//
//                    $scope.image_list = d;
//                    $scope.annotations = [];
//
//                    $.each($scope.image_list, function(n, image_data){
//
//                         var placeholder_obj = {
//                             annotationid: -1,
//                             steps: {}
//                         };
//                         $scope.annotations.push(placeholder_obj);
//                     });
//
//                    $scope.totalItems = $scope.image_list.length;
//
//                    $scope.selectImage(0);
//
//                    $scope.nextStep();
//
//                });
//            }
//        });




        // Accessors

        $scope.getCurrentStepConfig = function(){
            if ($scope.step >= 0) {
                return $scope.decision_tree[$scope.step]
            }

            return undefined;
        }

        $scope.getCurrentAnnotation = function(){

        	if($rootScope.applicationReady){

        		if ($scope.annotations) {
//                    console.log($scope.annotations[$scope.image_index]);
        			return $scope.annotations[$scope.image_index];
        		}

        	}
        	return undefined;
        }






        // selections

        $scope.selectImage = function(selected_index){

            $scope.image_index = selected_index;
            $scope.current_image = $scope.image_list[$scope.image_index];

            console.log($scope.current_image);

            $rootScope.active_image = $scope.current_image;

            //todo uncomment this eventually

            if($rootScope.imageviewer){
                $rootScope.imageviewer.clearPaintByNumber();
            }
        }





        $scope.stepHasDropDownOptions = function(){

            // returns true if current toolbar state is select
            if ($scope.tool_bar_state){
                return $scope.tool_bar_state == 'select' || $scope.tool_bar_state == 'rppaint';
            }
            return false;

        }


        $scope.canGoToNextStep = function() {

            // returns true if the current step contains the necessary information to go to the next step
            if ($scope.step == 0){

                // step 0 -> if we have an image
                return $rootScope.active_image != undefined;

            }
            else if ($scope.step == $scope.totalSteps -1 ){
                return true;
            }
            else if ($scope.step > 0){

                // step 1=6 -> if we have annotations
                return $scope.stepHasAnnotations($scope.step);
            }

            return false;
        }







        $scope.selectDropDownOption = function(option){

            if (option.type == 'drop'){

                console.log('this is not a valid selection');
            }
            else if (option.type == 'dropchoice') {

                console.log('valid selection, creating annotation and opening modal');

                var feature = new ol.Feature({
                    title: option.title,
                    longtitle: option.longtitle,
                    icon: option.icon,
                    source: 'selectedoption'
                });

                feature.setGeometry(new ol.geom.Point([0, 0]));

                $rootScope.imageviewer.setAnnotations([feature]);

                console.log($rootScope.imageviewer.getFeatures());



                if(option.options.length > 0){
                    // contains additional questions in form of modal
                    $scope.openModalWithOptions(option);

                }

            }
            else if (option.type == 'dropoption') {

                console.log('valid paint selection');

                $scope.selectDetail(option);

            }
            else if (option.type == 'gotostep') {

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

                console.log('unhandled option type')
                console.log(option);
            }




        }













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






        $scope.setDrawMode = function(newDrawMode, newDrawLabel){

            $scope.draw_mode = newDrawMode;
            $rootScope.imageviewer.setDrawMode(newDrawMode, newDrawLabel);

        }



        // setters

        $scope.saveCurrentStepAnnotation = function(){

            // just making things explicit for readability's sake
            var features = $rootScope.imageviewer.getFeatures();
            var current_step = $scope.step;
        	var currentAnnotation = $scope.getCurrentAnnotation();

            if (features.length){

                if(current_step in Object.keys(currentAnnotation.steps)){

                    // we have an existing annotation, just update the features and modify date
//                    var stepAnnotation = currentAnnotation.steps[current_step]

//                    var geojson  = new ol.parser.GeoJSON;
//                    var features = vectorsource.getFeatures();
//                    var json     = geojson.writeFeatures(features);

                    var singleAnnotation = {
                        features : features,
                        startTime : -1,
                        lastModifyTime : -1,
                        initialCreateTime : -1
                    };

                    currentAnnotation.steps[current_step] = singleAnnotation;

                }
                else
                {
                    // this is the first instance of the annotation, set the create date and field of view as well
                    console.log('this is the first annotation for this step, creating');

                    var singleAnnotation = {
                        features : features,
                        startTime : -1,
                        lastModifyTime : -1,
                        initialCreateTime : -1
                    };

                    currentAnnotation.steps[current_step] = singleAnnotation;
                }
            }
            else
            {
                if ($scope.step_config && $scope.step_config.type){

                    if ($scope.step_config.type == 'superpixel'){

                        var segmentationPackage = $rootScope.imageviewer.getSegmentationPackage();


                        $http.post('/api/v1/user/' + $rootScope.user_id + '/devnull', segmentationPackage).then(function(response){
                            console.log(response);
                        });


                        console.log($scope.regionpaint_size);

                        var feature = new ol.Feature({
                            title: 'superpixel',
                            longtitle: 'superpixel region',
                            icon: '',
                            source: '',
                            threshold: $scope.regionpaint_size
                        });

                        // set the geometry of this feature to be the screen extents
                        feature.setGeometry(new ol.geom.Point([0, 0]));

                        var f = new ol.format.GeoJSON();
                        var geojsonfeatures = f.writeFeatures([feature]);

                        var singleAnnotation = {
                            features : geojsonfeatures,
                            startTime : -1,
                            lastModifyTime : -1,
                            initialCreateTime : -1
                        };

                        currentAnnotation.steps[current_step] = singleAnnotation;
                    }

                }
            }

            console.log(currentAnnotation);
        };

        $scope.saveStepAnnotation = function(annotations, step_to_save){

        	var currentAnnotation = $scope.getCurrentAnnotation();
        	currentAnnotation.steps[step_to_save] = annotations;
        }

        $scope.getStepAnnotations = function(){

        	var currentAnnotation = $scope.getCurrentAnnotation();
        	console.log('current annotation', currentAnnotation);
            if(currentAnnotation){
                return currentAnnotation.steps[$scope.step]
            }
            return undefined;
        }

        $scope.getAllFeatures = function(){

            var currentAnnotation = $scope.getCurrentAnnotation();

            var all_features = [];

            for(var step in currentAnnotation.steps){
                if (step != $scope.totalSteps - 1){
                    for(var i =0; i < currentAnnotation.steps[step].features.length; i++){
                        all_features.push(currentAnnotation.steps[step].features[i]);
                    }
                }
            }

        	return all_features;

        }



        $scope.beginAnnotation = function(){

            // clear paint layer if present, then call next step

            if($rootScope.imageviewer){
                $rootScope.imageviewer.clearPaintByNumber();
            }

            $scope.review_mode = false;

            $scope.nextStep();

        }

        $scope.nextStep = function(){

            // if we have the step config, use it to define next step
            if($scope.step_config){

                if($scope.step_config.next != $scope.step){
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
        }


//        $scope.clearstep = function(){
//
//            console.log('clear step and reload');
//
//        }

        $scope.previousStep = function(){

            if($scope.step > 0){
                $scope.gotoStep($scope.step-1);
            }


        }

        $scope.showHelp = function(help_val)
        {
            alert('help!');
        }

        $scope.manualEdit = function(){

            $scope.tool_bar_state = 'pldefine';
            $scope.setDrawMode('pointlist', 'lesion');

        }



        $scope.increaseParameter = function(){

            if($scope.tool_bar_state == 'mwdefine'){
                $scope.magicwand_tolerance += 5;
                $scope.imageviewer.setFillParameter($scope.magicwand_tolerance);
                $scope.imageviewer.regenerateFill();
            }
            else if ($scope.tool_bar_state == 'spconfirm'){

                $scope.regionpaint_size += 5;
                $scope.imageviewer.setPaintParameter($scope.regionpaint_size);
                $scope.imageviewer.clearPaintByNumber();
                $scope.runRegionPaintConfigure();
                //

            }
        }

        $scope.decreaseParameter = function(){

            if($scope.tool_bar_state == 'mwdefine'){

                if($scope.magicwand_tolerance >= 5){
                    $scope.magicwand_tolerance -= 5;
                }
                else {
                    $scope.magicwand_tolerance = 0;
                }

                $scope.imageviewer.setFillParameter($scope.magicwand_tolerance);
                $scope.imageviewer.regenerateFill();
            }
            else if ($scope.tool_bar_state == 'spconfirm'){

                if($scope.regionpaint_size >= 5){
                    $scope.regionpaint_size -= 5;
                }
                else {
                    $scope.regionpaint_size = 0;
                }

                $scope.imageviewer.setPaintParameter($scope.regionpaint_size);
                $scope.imageviewer.clearPaintByNumber();
                $scope.runRegionPaintConfigure();

                //
            }
        }








        // initial function when a step is loaded
        $scope.loadStep = function(){

            // get current step configuration
            $scope.step_config = $scope.getCurrentStepConfig();


            // clear viewer current and temporary annotations
            $scope.clearStep();

            if($scope.step_config && $scope.step_config.type == 'end'){

                $scope.review_mode = true;

                var allFeatures = $scope.getAllFeatures();

                if (allFeatures) {
                    $rootScope.imageviewer.setAnnotations(allFeatures);
                }
                else {
                    // this step doesn't have annotations, do appropriate step selection processing steps (aka auto)
                }
            }
            else {

                console.log('Not the last step in the process')

                var stepAnnotation = $scope.getStepAnnotations();

                if (stepAnnotation) {

                    $rootScope.imageviewer.setAnnotations(stepAnnotation.features);

                    $scope.select_pattern = stepAnnotation.features[0];

                    console.log($scope.select_pattern);

                }
                else {

                    // this step doesn't have annotations, do appropriate step selection processing steps (aka auto)

                }


            }




            // load previous annotations if there are any
            $rootScope.imageviewer.hidePaintLayerIfVisible();


            if($scope.step_config){


                // set imageviewer to current step configuration
                if ($scope.step_config.default != "") {

                    $scope.setDrawMode($scope.step_config.default, $scope.step_config.classification);
                }
                else {
                    $scope.setDrawMode('navigate', '');
                }

                if($scope.step_config.zoom == "lesion"){

                    var feature = $scope.getLesionFeature();
                    $rootScope.imageviewer.moveToFeature(feature);

                }


                // set some UI helpers
                $scope.step_options = $scope.step_config.options;
                $scope.step_base = $scope.step_config.step;

                console.log('Finished loading step', $scope.step_config.step);


            }


        }



        $scope.clearStep = function(){

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

        }


        // returns the first feature from the first lesion definition step
        $scope.getLesionFeature = function(){
            var currentAnnotation = $scope.getCurrentAnnotation();

            return currentAnnotation.steps[1].features[0];

        }

        // this will clear the
        $scope.clearLayerAnnotations = function(){
            $rootScope.imageviewer.clearLayerAnnotations();
        }

        $scope.clearDrawingTools = function(){
            $rootScope.imageviewer.hidePaintLayerIfVisible();
            $rootScope.imageviewer.removeDrawInteraction();
        }

        // This clears the selection stack for overall pattern
//        $scope.clearStackAnnotations = function(){
//
//            clear the selection stack
//            $scope.select_stack = [];
//            $scope.select_last = undefined;
//
//            if($scope.step_config){
//
//                $scope.step_base = $scope.step_config.step;
//                $scope.step_options = $scope.step_config.options;
//
//            }
//        }



        $scope.gotoStep = function(step){

            if (step < $scope.totalSteps) {

                // pre step change transition
                $scope.saveCurrentStepAnnotation();

                $scope.step = step;

                $scope.loadStep();

            }
            else if (step == $scope.totalSteps) {

                $scope.clearStep();

                // get a copy of the annotation
                var annotation = $scope.getCurrentAnnotation();

                var annotation_to_store = {};
                annotation_to_store['image_id'] = JSON.stringify($scope.current_image.record_id);
                annotation_to_store['image'] = $scope.current_image;
                annotation_to_store['user_id'] = JSON.stringify($rootScope.user_id);
                annotation_to_store['steps'] = {};

                var f = new ol.format.GeoJSON();

                for(var k in annotation.steps){

                    annotation_to_store.steps[k] = {};
                    var stepFeatures  = annotation.steps[k].features;

                    annotation_to_store.steps[k]['features'] = f.writeFeatures(stepFeatures);
                }

                var self = this;

                var annotation_url = '/api/v1/user/' + $rootScope.user_id + '/taskcomplete/markup';

                $http.post(annotation_url, annotation_to_store).success(function(response){

                    if(response.annotation_id){
                        if($scope.current_image.annotation){
                            $scope.current_image.annotation.push(response.annotation_id);
                        }
                        else{
                            $scope.current_image.annotation = [response.annotation_id];
                        }
                    }

                	$scope.step = 0;
                    $scope.step_config = undefined;

                    $scope.review_mode = false;

                    $scope.clearStep();
                    $scope.loadStep();

                });
            }
        }




// Paint by numbers methods


        $scope.runRegionPaint = function(){

            $scope.runningSegmentation = true;

            $timeout(function(){

                $scope.regionPaintDelay();

            }, 50);
        };

        // TODO consider combining independent functions into switched

        $scope.runRegionPaintConfigure = function(){

            $scope.runningSegmentation = true;

            $timeout(function(){

                $scope.regionPaintConfigureDelay();

            }, 50);
        };

        $scope.regionPaintConfigureDelay = function(){

            $scope.tool_bar_state = 'spconfirm';

            var feature = $scope.getLesionFeature();
            $rootScope.imageviewer.moveToFeature(feature);

            $scope.setDrawMode('none', '');

        	$rootScope.imageviewer.startPainting();

            $scope.runningSegmentation = false;
        };


        $scope.regionPaintDelay = function(){

            $scope.tool_bar_state = 'rppaint';

            var feature = $scope.getLesionFeature();
            $rootScope.imageviewer.moveToFeature(feature);

            $scope.setDrawMode('paintbrush', '');

        	$rootScope.imageviewer.startPainting();

            $scope.runningSegmentation = false;
        };

        $scope.finishRegionPaint = function(){

			$scope.tool_bar_state = 'rpreview';
            $rootScope.imageviewer.acceptPainting();

        }

        $scope.cancelRegionPaint = function(){

        	$rootScope.imageviewer.acceptPainting();

//        	$rootScope.imageviewer.clearTemporary();

        	$scope.resetStep();
        };

        $scope.navMode = function(){

            $rootScope.imageviewer.hidePaintLayerIfVisible()
            $scope.setDrawMode('navigate', '');

        };

        $scope.drawMode = function(){

            var feature = $scope.getLesionFeature();
            $rootScope.imageviewer.moveToFeature(feature);
            $rootScope.imageviewer.showPaintLayerIfVisible();
            $scope.setDrawMode('paintbrush', '');


        };




// Magic wand methods

//        $scope.startMagicWand = function(){
//            $scope.tool_bar_state = 'mwdefine';
//            $scope.setDrawMode('autofill');
//        }



        $scope.selectDetail = function(detailobj){
            $scope.select_detail = detailobj;
            $rootScope.imageviewer.selectAnnotationLabel(detailobj.value);
        }


//		$scope.selectOption = function(key, option_to_select) {
//
//            console.log('EH');
//
//			var selected_url = 'static/derm/' + $scope.step_base + '/' + (key+1) + '.jpg'
//
//			console.log('selected url', selected_url)
//
//			var select_single = {
//				url : selected_url,
//				key : key
//			}
			
//			if(option_to_select.type == 'select'){
//
//				$scope.select_stack.push(select_single);
//				$scope.step_options = option_to_select.options;
//				$scope.step_base = $scope.step_base + '/' + (key+1);
//
//			}
//			else if (option_to_select.type == 'review') {
//
//				$scope.select_stack.push(select_single);
//	        	$scope.tool_bar_state = option_to_select.type;
//                $scope.openModalWithOptions(option_to_select);
//
//			}
//            else if (option_to_select.type == 'gotostep'){
//
//                $scope.select_stack.push(select_single);
//                $scope.gotoStep(option_to_select.value);
//
//            }


//			else if (option_to_select.type == 'selectadvanced') {
//
//				$scope.select_last = select_single;
//
//				// $rootScope.imageviewer.saveSelectionStack($scope.select_stack);
//
//				$scope.step_options = option_to_select.options;
//
//				$scope.step_base = $scope.step_base + '/' + (key+1);
//
//	        	$scope.tool_bar_state = option_to_select.type;
//
//
//			}
//			else if(option_to_select.type == 'next') {
//
//				console.log('proceeding to next step');
//
//				$scope.nextStep();
//
//			}
//		}


        var ModalInstanceCtrl = function ($scope, $modalInstance, options) {

            $scope.base = options;
            $scope.selectOption = function(opt){

                $modalInstance.close(opt);

            }

        };



        $scope.openModalWithOptions = function(options){

//            console.log(options)

            $scope.modal_options = options.options[0]

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

        }

        $scope.deleteSaved = function(key){

            if ($rootScope.applicationReady)
            {
            	var current_annotation = this.getCurrentAnnotation();

                if(current_annotation){
                    if (current_annotation.steps.hasOwnProperty(key)){
                        delete $scope.annotations[$scope.image_index].steps[key];
                    }
                }

//                $scope.clearLayerAnnotations();
//
//                $scope.select_detail = undefined;
//                $scope.select_pattern = undefined;
//
                $scope.clearStep();
            }

            return false;
        }

        // state functions
        $scope.showIfStep = function(step){

            return parseInt(step) == $scope.step;
        }


        $scope.smartShowHeader = function(step, details){

            // if the step has annotations, return yes
            if($scope.stepHasAnnotations(step)){

                if($scope.review_mode){
                    return true;
                }
            }

            if(step == $scope.totalSteps -1){
                if($scope.review_mode){
                    return true;
                }
            }

            // depending on
            return parseInt(step) == $scope.step;
        }


        $scope.smartShowContent = function(step, details){



// if the step has annotations, return yes
//            if($scope.stepHasAnnotations(step)){
//                return true;
//            }

//            if($scope.isLastStep()){
//                return true;
//            }


            // depending on

            return parseInt(step) == $scope.step;
        }

        $scope.isLastStep = function(){

            return ($scope.step == ($scope.totalSteps - 1));

        }


        $scope.showIfStepGTE = function(step){

        	return parseInt(step) <= $scope.step;	
        }

        $scope.showIfStepOrLast = function(step){

            if($scope.step == $rootScope.decision_tree.length - 1 ){

                return true;
            }

            return parseInt(step) == $scope.step;
        }

        $scope.compareState = function(target, current_value){
            return target == current_value;
        }



        // if there are any annotations, you can proceed
        $scope.hasAnnotations = function(){
            return ($scope.hasLayerAnnotations() || $scope.hasStackSelections());
        }

        $scope.imageHasAnnotations = function(index){

            if ($rootScope.applicationReady)
            {
                if($scope.image_list[index].annotation){
                    return true;
                }
            }
            return false;
        }

        //temporary annotations = points that need to be converted into a polygon
        $scope.hasStackSelections = function(){

            if ($rootScope.applicationReady)
            {
                return $scope.select_stack.length > 0;
            }
            return false;
        }

        // saved annotations = points that have been converted... NOT TO BE CONFUSED WITH STEP annotations
        $scope.hasLayerAnnotations = function(){
            if ($rootScope.applicationReady)
            {
                return $rootScope.imageviewer.hasLayerAnnotations();
            }
            return false;
        }

        $scope.stepHasAnnotations = function(step){

            if ($rootScope.applicationReady)
            {
                if(step != $scope.totalSteps -1 ){

                    var current_annotation = this.getCurrentAnnotation();

                    if ($rootScope.imageviewer.hasLayerAnnotations()){
                        if (step == $scope.step){
                            return true;
                        }
                    }

                    if (current_annotation) {

                        var step_annotation = current_annotation.steps[step];



                        if(step_annotation){
                            return true;
                        }
                    }

                }

            }
            return false;
        }







        $scope.updateCompleteState = function() {

            if($rootScope.annotation_list.length > 0)
            {
                // update current image state
                var o = $rootScope.annotation_list[$rootScope.image_index];
                var is_complete = true;
                is_complete = o.step[1].length > 0 && is_complete;
                is_complete = o.step[2].length > 0 && is_complete;
                is_complete = o.step[3].length > 0 && is_complete;
                // is_complete = o.details.length > 0 && is_complete;

                o.complete = is_complete;

                // recalculate the total complete count
                var completed = 0;

                $.each($rootScope.annotation_list, function(n, subject_data){

                    if(subject_data.complete == true){
                        console.log('complete: ', subject_data);
                        completed +=1;
                    }
                });

                return completed;
            }
            return 0;
        }


        $scope.drawModeIs = function(mode_query) {

            if($rootScope.applicationReady)
            {            
                return mode_query == $scope.draw_mode;
            }
            return false;
        }



    }]);





var annotationView = derm_app.controller('AnnotationView', ['$scope', '$rootScope', '$timeout',

    function ($scope, $rootScope, $timeout) {


    }]);





// utilities
var studyToImageSource = function (study_num) {
    var src = "http://dermannotator.org/cgi-bin/iipsrv.fcgi?DeepZoom=/RAW_IMAGE_DATA/bigdata2/PYRAMIDS/MSKCC/BATCH1/B1/"
            + study_num + ".tif.dzi.tif.dzi";
//    console.log(src);
    return src;
};


var iff_filter = derm_app.filter('iif', function () {
   return function(input, trueValue, falseValue) {
        return input ? trueValue : falseValue;
   };
});


// drag and drop list directive
// directive for a single list
// based on code from
// http://www.smartjava.org/content/drag-and-drop-angularjs-using-jquery-ui
var dndList = derm_app.directive('dndList', function() {

    return function(scope, element, attrs) {

        // variables used for dnd
        var toUpdate;
        var startIndex = -1;

        // watch the model, so we always know what element
        // is at a specific position
        scope.$watch(attrs.dndList, function(value) {
            toUpdate = value;
        },true);

        // use jquery to make the element sortable (dnd). This is called
        // when the element is rendered
        $(element[0]).sortable({
            items:'li',
            start:function (event, ui) {
                // on start we define where the item is dragged from
                startIndex = ($(ui.item).index());
            },
            stop:function (event, ui) {
                // on stop we determine the new index of the
                // item and store it there
                var newIndex = ($(ui.item).index());
                var toMove = toUpdate[startIndex];
                toUpdate.splice(startIndex,1);
                toUpdate.splice(newIndex,0,toMove);

                // we move items in the array, if we want
                // to trigger an update in angular use $apply()
                // since we're outside angulars lifecycle
                scope.$apply(scope.model);
            },
            axis:'y'
        })
    }
});



// data sources

var imageList = derm_app.factory('imageList', function($http) {

  // shuffle from SO: http://stackoverflow.com/questions/2450954/how-to-randomize-shuffle-a-javascript-array
  function shuffle(array) {
      var currentIndex = array.length
        , temporaryValue
        , randomIndex
        ;

      // While there remain elements to shuffle...
      while (0 !== currentIndex) {

        // Pick a remaining element...
        randomIndex = Math.floor(Math.random() * currentIndex);
        currentIndex -= 1;

        // And swap it with the current element.
        temporaryValue = array[currentIndex];
        array[currentIndex] = array[randomIndex];
        array[randomIndex] = temporaryValue;
      }

      return array;
  }

  var imageList= {
    fromStaticJSON: function() {
        var url = 'static/data/json_subj_list.json';
            var promise = $http.get(url).then(function (response) {
          return response.data;
        });
      return promise;
    },

    // fromDB -> perform API request with user_id, image offset, count to get, and whether it should be shuffled
    fromDB: function(user_id, offset, count, shouldShuffle) {
        console.log('Query:: fromDB: ' + user_id + " " + offset + " " + count + " " + shouldShuffle)
//        var url = 'static/data/json_subj_list.json';
            var url = 'images/' + offset + "/" + count + "/";

            var promise = $http.get(url).then(function (response) {

            if(shouldShuffle){
//                return shuffle(response.data.slice(offset,count));
                return shuffle(response.data);
            }
            else
            {
//                return response.data.slice(offset, count);
                return response.data;
            }
        });
      return promise;
    },
    noAnnotations: function(user_id, offset, count, shouldShuffle) {
        console.log('Query:: fromDB: ' + user_id + " " + offset + " " + count + " " + shouldShuffle)
//        var url = 'static/data/json_subj_list.json';
            var url = 'newimages/' + offset + "/" + count + "/";

            var promise = $http.get(url).then(function (response) {

            if(shouldShuffle){
//                return shuffle(response.data.slice(offset,count));
                return shuffle(response.data);
            }
            else
            {
//                return response.data.slice(offset, count);
                return response.data;
            }
        });
      return promise;
    },
    withAnnotations: function(user_id, offset, count, shouldShuffle) {
        console.log('Query:: fromDB: ' + user_id + " " + offset + " " + count + " " + shouldShuffle)
//        var url = 'static/data/json_subj_list.json';
            var url = 'annotatedimages/' + offset + "/" + count + "/";

            var promise = $http.get(url).then(function (response) {

            if(shouldShuffle){
//                return shuffle(response.data.slice(offset,count));
                return shuffle(response.data);
            }
            else
            {
//                return response.data.slice(offset, count);
                return response.data;
            }
        });
      return promise;
    }
    };

  return imageList;
});





var decisionTree = derm_app.factory('decisionTree', function($http) {

  var decisionTree= {
    fromServer: function() {
        var url = 'http://example.com/json.json';
            var promise = $http.jsonp(url).then(function (response) {

                console.log(response.data);
          return response.data;
        });
      return promise;
    },
    fromLocal: function() {
        var url = 'static/derm/decisiontree.json';
            var promise = $http.get(url).then(function (response) {
          return response.data;
        });
      return promise;
    }

    };

  return decisionTree;
});




// handle window resize events
function updateLayout() {

    $("#angular_id").height(window.innerHeight);
    $("#annotationView").height(window.innerHeight);


    var scope = angular.element($("#angular_id")).scope();
    scope.safeApply(function(){


        console.log(window.innerWidth, window.innerHeight);
        //1920 1106
    })
}

function externalApply() {
    var scope = angular.element($("#angular_id")).scope();
    scope.safeApply(function(){
    })
}

function toggleDebug() {

    var scope = angular.element($("#angular_id")).scope();

    console.log('Angular state before: ', scope.debug);

    scope.safeApply(function(){

       scope.debug = !scope.debug;

    })

    console.log('Angular state before: ', scope.debug);

}

window.onresize = updateLayout;














