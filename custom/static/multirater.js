//These functions were written by David A Gutman MD PhD Emory University
// Code is to help load and process data and load and manipulate SVG elements corresponding to user markups
function random(range) {
    return Math.floor(Math.random() * range);
}


//sample images uda2pilot isic_0001135

//54e771eabae47850e86ce39d   this is a segmentation... probably need supserpixels as well...
//"imageId": "54e755ffbae47850e86ce076",


function loadSVGTileData(imageName) {
    console.log('need to load svg data for' + imageName);
    SVG_file = image_info_list[imageName].superpixel_svg;
    img_height = image_info_list[imageName].img_height;
    img_width = image_info_list[imageName].img_width;

    new_geodata = function() {
        console.log('loading new geo data');
        geo_array = [];
        $.ajax({
            'async': false,
            'global': false,
            'url': SVG_file,
            'dataType': "json",
            'success': function(result) {
                $.each(result, function(i, contour) {
                    geo_array.push(JSON.parse(contour))
                });
                //GEO ARRAY IS NOW generated with contours... so can call another function to generate an SVG layer a well // 
            }
        });

        return geo_array;
    }();


    //  This will iterate through all the tiles and color them a different color to show the tile overlays
    $(".tileClass").remove();

    my_points = contourdata_to_shape(new_geodata, img_width);



    //This generates the pretty multicolor tile image
    $.each(my_points, function(k, point_list) {
        d3.select(svg_layer.node()).append("polygon").attr("points", point_list.coords).style('fill', 'none').attr('opacity', 0.5).attr('class', 'tileClass').attr('id', 'tile' + point_list.labelindex)
    });
}


function new_mark_superpixels(sp_info) {
    $(".tileClass").css('fill', 'none');

    //need to add in the current_feature
    if (superpixel_markup_info[current_feature]) {
        num_superpixels = Object.keys(superpixel_markup_info[current_feature]).length;
    } else {
        return;
    }

    // console.log(num_superpixels)
    $("#tile_info_stats").empty(); /// clear the current DIV before I start putting stats in it..
    //        $("#tile_info_stats").append(num_superpixels.toString() + ' superpixels are in this image');
    //This code is very sensitive to on load events...
    $.each(superpixel_markup_info[current_feature], function(tileID, rater_data) {
        //         ///I am now iteration over each tile in the selected Image...
        tileAnnotated = false;
        raters_for_tile = [];

        //So because of the way we store the data, I need to iterate through each superpixel and determine which rater(s) marked it up.. then color things
        $.each(rater_data, function(r, v) {
            if (v != "0.0") {
                //                        console.log(r,v,tileID);
                tileAnnotated = true;
                raters_for_tile.push(r);
            }
        });

        if (tileAnnotated) {
            //Now that I know the tile has been annotated, I need to render the results
            //console.log(raters_for_tile, tileID);

            if (raters_for_tile.length == 1) {
                //In this case the tile is colored for the individual rater.... otherwise it's a color palette
                //Currently I am going 
                //var a = fruits.indexOf("Apple");
                rater_index = raters.indexOf(raters_for_tile[0])
                    // console.log(raters_for_tile,rater_index)

                $("#tile" + tileID).css('fill', colours[rater_index]);

            } else {
                $("#tile" + tileID).css('fill', color_heatmap[raters_for_tile.length]);
            }
        }

    });


    $(".tileClass").hover(function() {
        //  console.log(this.id);
        pixnum = (this.id).substring(4);
        $("#tile_info_stats").empty(); /// clear the current DIV before I start putting stats in it..
        //              $("#tile_info_stats").append(num_superpixels.toString() + ' superpixels are in this image');
        $("#tile_info_stats").append("<br>You are hovering on sp: " + this.id);


        tile_num = this.id.substring(4); //need to turn the tileID which actually is tile234 or similar into only the number part.. so skip the first 4 chars
        //Determine who marked up this file
        pix_raters = superpixel_markup_info[current_feature][tile_num];
        //remember this may contain ALL raters who assessed this feature, so need to make sure there's not a "0.0" there which means that rater
        //didn't actually mark that specific superpixel with the given feature
        rft = []
        $.each(pix_raters, function(k, v) {
                if (v != '0.0') {
                    rft.push(k);
                }
            })
            //console.log(rft);
        $("#tile_info_stats").append("<br>Raters: " + JSON.stringify(rft));


    });

};


function lesionboundary_to_svgshape( lesionBoundary_Dict, img_width)
{
    //Probably should come this with the function below..
    scale_factor = 1;
    polygon_list = [];
    console.log('should be trying to render the boundary now!?');
    console.log(lesionBoundary_Dict);
    //Openseadragon uses the image width for bo the x and y scale factor... probably should rename this pixel factor
    x_scale_factor = 1.0 / img_width;
    y_scale_factor = 1.0 / img_width;

    $(".boundaryClass").remove();

    // $.each(contours, function(index, contour) {
    //     coord_info = contour.geometry.coordinates;
            coord_info = lesionBoundary_Dict.lesionBoundary.geometry.coordinates[0];
            console.log(coord_info);
         coord_string = "";
         $.each(coord_info, function(k, v) {
                 console.log(k,v[0],v[1]);
                 coord_string += `${(v[0]* x_scale_factor ) },${ ( v[1] * y_scale_factor) } `;
             }) // the |0 made them all integers
         console.log(coord_string);
       // polygon_svg_str = `<polygon points="${coord_string}" style="fill:${colours[ random(9)]};stroke;purple;stroke-width:1;opacity:0.5" id="boundary0" class="boundaryClass" />`;
    //     labelindex = contour.properties.labelindex;
         d3.select(svg_layer.node()).append("polygon").attr("points", coord_string).style('fill', 'blue').attr('opacity', 0.2).attr('class', 'boundaryClass').attr('id', 'boundary0');
         //.attr('stroke','blue');
    // });
    //     polygon_list.push({
    //         'coords': coord_string,
    //         'labelindex': contour.properties.labelindex
    //     });
    // });

    // return svg_shape;

}

function contourdata_to_shape(contours, img_width) {
    scale_factor = 1;
    polygon_list = [];

    //Openseadragon uses the image width for bo the x and y scale factor... probably should rename this pixel factor
    x_scale_factor = 1.0 / img_width;
    y_scale_factor = 1.0 / img_width;

    $.each(contours, function(index, contour) {
        coord_info = contour.geometry.coordinates;

        coord_string = "";
        $.each(coord_info, function(k, v) {
                coord_string += `${(v[0]* x_scale_factor ) },${ ( v[1] * y_scale_factor) } `;
            }) // the |0 made them all integers

        polygon_svg_str = `<polygon points="${coord_string}" style="fill:${colours[ random(9)]};stroke;purple;stroke-width:1;opacity:0.5" id="tile${contour.properties.labelindex}" class="tileClass" />`;
        labelindex = contour.properties.labelindex;

        polygon_list.push({
            'coords': coord_string,
            'labelindex': contour.properties.labelindex
        });
    });

    //Need to add the below function to a callback function for above..
    $(".tileClass").hover(function() {
        console.log(this.id)
    });
    return polygon_list;
}


//Currently not actually doing anything with the feature.. or rater...!! need to add in handlers
function color_some_tiles(rater, feature) {
    //given a feature and a rater and an image ID I should color the respective tiles on the super pixel image
    console.log("should be painting " + feature + "for " + rater);
    new_mark_superpixels(); // loadSVGTileData(imageName);
    //I think I am going to structure this to paint all tiles for all the raters...
}

function show_all_tiles() {
    //This will iterate through all the tiles and color them a different color to show the tile overlays
    //s$(".tileClass").remove()
    $(".tileClass").css('fill', function() {
        pixnum = this.id.substring(4);
        console.log(pixnum);
        return color20((pixnum % 20))
    });
}

function load_image_list(study_uid) {

    var get_img_list_url = 'https://isic-archive.com/api/v1/study/' + study_uid + '/images/';

    $.getJSON(get_img_list_url, function(data) {
        new_img_list = data;
        //This currently returns an _id and a name _id: "54e77f6fbae478166c01e546"  name: "ISIC_0001160"
        //TO DO:  Load the image data now??
        ///Need to remember to first clear the image list
        //Now I need to iterate through each item and add it to the image list...
        first_imageuid = ''

        $("#image_list_dd").empty();
        $.each(new_img_list, function(k, v) {
            if (k == 0) {
                first_imageuid = v['_id']
            };
            var new_img = `<option id="${v['_id']}" value="${v['_id']}">${v['name']}</option>`;
            $("#image_list_dd").append(new_img);
        })
        $("#image_list_dd").select2(); //Reinitialize the dynamic search widget

        //console.log('should be trying to load', first_imageuid);
       //So I now need to actually get some metadata for the first image, which then calls another function to load the data..
        get_image_data(first_imageuid);

    });

}

function load_avail_studies() {
    //This requires no parameters ; this gets the available study data
    first_studyid = ''; //Will keep track of the first_studyid and once the data is loaded, load the image set associated with it

    $.getJSON(study_url, function(data) {
        avail_studies = data;
        //I am going to disable buttons on the feature list if that feature isn't present in the currnet image...
        //console.log(avail_studies)
        //Also now load the feature button by iterating through them
        $.each(avail_studies, function(k, v) {
                //      console.log(v,k);
                if (k == 0) {
                    first_studyid = v['_id']
                };

                dtoa = '<option id="' + v['_id'] + '" value="' + v['_id'] + '">' + v.name + '</option>'
                $("#data_source_dd").append(dtoa);
                avail_studies_dict[v.name] = v;
            })
            //Now that I have a list of all available studies, I can go ahead and populate the image list
            //This should use the function I defined above..
        load_image_list(first_studyid);
        //console.log
        load_feature_list(first_studyid); //This will populate the feature widget..
        load_rater_list(first_studyid); //I think this is another endpoint...
        return (avail_studies);
    });
}


function load_feature_list(cur_study_uid) {
    //AJAX Call to hit the API EndPoint and get the list of features for the given project and/or Image
    //I think to make the UI cleaner and so the buttons don't move around, we will load all of the buttons associated
    //with a project...
    avail_features = []
        //I need to determine the featureset uid for this study
    $.each(avail_studies, function(i, v) {
        console.log(i, v);
        console.log(v.meta.featuresetId);
        if (v['_id'] == cur_study_uid) {
            featureset_uid = v.meta.featuresetId;
        } //Probably should do a break here??
    })

    $.getJSON('https://isic-archive.com/api/v1/featureset/' + featureset_uid, function(data) {
        console.log(data)
        avail_features = data['region_features'];
        //I am going to disable buttons on the feature list if that feature isn't present in the currnet image...
        console.log("newly available features are");
        console.log(avail_features)
            //Probably put the code to create the widget her eas well?
        current_feature_set = avail_features;
        create_featurelist_widget(current_feature_set, feature_groups, 'feature_accordion');
    });
}

function create_featurelist_widget(full_feature_set, feature_grouping, widget_div) {
    //This will actually create the widget of buttons associated with a set of features
    //This creates an accordion, and will group the buttons based on a "top leavel" feature
    //which also serves as the name of the individual accordion piece
    //Clear the current widget
    if (  $("#"+widget_div).accordion('instance') )
            { $("#"+widget_div).accordion('destroy') };

    $("#"+widget_div).empty();


    $.each(feature_grouping, function(idx, cur_grp) {
        //So this actually creates the Top Level labels for the accordion widget, buttons need to be added after these are craetd
        console.log(idx, cur_grp);
        //First thing I need to do is create an h3 (or h4 ) tag for the group
        $("#" + widget_div).append(` <h4>${cur_grp['feature_group']}</h4><div id="featbtn_${cur_grp['feature_group']}"></div>`);
        //Now I need to figure out which buttons to add to this feature
        //TO DO:  REMEMBER F THE FEATURE GROUP HAS A SPACE... JAVASCRIPT WILL EXPLODE

        button_data_for_cur_grp = [];
        $.each(full_feature_set, function(idx, feat) {
            //print "Should be lookining for";
            //console.log( cur_grp.feature_abbrev,feat);
            //  console.log(feat);

            //There are noew properties now... need to see if i should look at the check box features or other properties
            if (feat['id'].startsWith(cur_grp.feature_abbrev)) {
                feat_without_class = feat['id'].replace(cur_grp.feature_abbrev + '_', '');
                //To save Space I am removing the feature Class i.e. net col oth
                //TO DO:  Need to figure out/clarify what class I should put this in so it actually displays
                var rb = `  <button class="feature_btns btn btn-xs" style="font-size:10px" data-toggle="tooltip" data-placement="top" title="${feat['id']}" id="feat_${feat['id']}" value="${feat['id']}" >${feat_without_class}</button>`;
                button_data_for_cur_grp += rb;
            }
            //Now push the new radio buttons to that div
        });
        $("#featbtn_" + cur_grp['feature_group']).append(button_data_for_cur_grp);

    });
    $("#" + widget_div).accordion({
        collapsible: true
    });
    //The accordion has now been created, add click handlers to the buttons
    // annotated_feature_list = avail_features;


    annotated_feature_list = avail_features;

    $("#feature_accordion button").click(function() {
        console.log(this.id); // points to the clicked input button
        current_feature = this.value;
        $("#feature_info_stats").empty();
        //ALSO ADDI N SOME STATS TO INDICATE HOW MANY TILES WERE MARKED FOR THIS FEATURE...
        cfd = superpixel_markup_info[current_feature]; //Current Feature data
        if (!cfd) {
            $("#feature_info_stats").append("Feature " + current_feature + " NOT in this image");
        } else {
            $("#feature_info_stats").append("Feature" + current_feature + " present");
        }
        //     //So I need to check the state of the button to either draw or clear a given tile(s) colors for a rater..
        cur_slider_value = OpacitySlider.val();
        cur_opacity = 100;
        var new_opacity = (cur_opacity == 0) ? cur_slider_value : 0;
        $('.tileClass').attr('opacity', cur_slider_value);
        new_mark_superpixels();
        //hide_unannotated_features(superpixel_markup_info);
    });
}


function get_image_annotation_data(study_id, image_id) {
    //So in order for the UI to function properly, I need to grab all of the annotations available for the currnetly displayed image, and then build
    //a new object that contains some summary information for the image...

    //The Study ID can be obtained from
    $("#data_source_dd").val();

    annotationsAvailable = 'https://isic-archive.com/api/v1/annotation?studyId=' + study_id + '&imageId=' + image_id + '&details=true';

    //Now get all available annotations     Please note, by adding the details=true I get all the annotations in a single query
    //without that, I will jsut get the ID of the individual annotations

    $.getJSON(annotationsAvailable, function(data) {
        avail_annotations = data;
        //I am going to disable buttons on the feature list if that feature isn't present in the currnet image...
        console.log("newly available annotations are");
        console.log(avail_annotations)

        ftl = generate_image_annotation_summaries(avail_annotations);

        hide_unannotated_features(ftl); //Need to make sure this async is set properly.. may need to call this function
        //within the GIAS function
    })
}


//     //Probably put the code to create the widget her eas well?
//     // current_feature_set = avail_features;
//     // create_featurelist_widget(current_feature_set, feature_groups, 'feature_accordion');
// });


function generate_image_annotation_summaries(image_annotation_data) {
    /* So I should be passed an array that contains information about all the annotation data for the current data
    I need to parse this and figure out which feature(s) have been marked up for the current image...*/

    //console.log(image_annotation_data);
    rater_data = []; //This will keep track of the raters that have marked up this particular image...
    total_tiles = null; //This keeps track of the number of tiles and/or superpixels in the image... 

    features_seen_in_image = {};
    tile_data = {}
        //http://localhost:1234/api/TileInfo/ALL/UDA2_pilot_060  Thsi basically shows me how I created the data...

    //Each annotation ahs image features and region features... for now I'll just focus on region features
    $.each(image_annotation_data, function(k, v) //this cycles through all of the available annotations
        {
            $.each(v.annotations.region_features, function(idx, rf) {
                var sum = rf.reduce(function(a, b) {
                    return a + b;
                }, 0);
                //So in some cases, even though there's an annotation created for a feature, it turns out to be full of zeroes, so i wanna skip these
                if (sum > 0) {
                    features_seen_in_image[idx] = (features_seen_in_image[idx] || 0) + 1;
                }
                tiles = rf.length; //may want to add a check and make sure all the tiles are the same length???
            })
        }
    )

    //Now that i now the features seen in the image, I can create a combined array for each tile.... may want to refactor this at some point

    feature_tilelevel_info = {}

    $.each(Object.keys(features_seen_in_image), function(k, cur_feature) {
        //console.log("Generating compiled data for", cur_feature)
        feature_tilelevel_info[cur_feature] = {}; //Initialize the dictionary for the current feature

        //I now need to initialize this so that each tile has an element created
        for (i = 0; i <= tiles; i++) {
            feature_tilelevel_info[cur_feature][i] = {};
        } //Initialize the dictionary 

        //Now I need to iterate through each raters annotation...
        $.each(image_annotation_data, function(ak, av) {
            cur_rater = av.user.login;
            cur_region_data = av.annotations.region_features
            if (cur_region_data[cur_feature]) {
                //So it's possible that this feature might not actually be annotated/available in a given annotation
                //so this makes sure the key exists..
                //So now I need to actually add some data about the individual tile!! yeah
                feat_tileData = cur_region_data[cur_feature];
                $.each(feat_tileData, function(tileID, rater_score) {
                    feature_tilelevel_info[cur_feature][tileID][cur_rater] = rater_score;
                })

            }
           // console.log(ak, av);
        })
        //console.log(feature_tilelevel_info);

    });

    //So now that I have the summary data... I guess I can go ahead an update the image???feat

    return (feature_tilelevel_info);
}

function hide_unannotated_features(superpixel_markup_info) {
    //console.log('should be hiding buttons');
    //Beacause we may have 30-50 features present, we do not want the observer to try and click on each button to "see" if a given feature is there
    //First I need to reset all the radio buttons to make them all clickable, then disable if not present
    //$("#feature_btn_group").button('reset');
    //avail_features list the features that have been detected in this image..
    img_avail_features = Object.keys(superpixel_markup_info);
    //var annotated_feature_list = ['net_typ', 'net_atyp', 'str_chrys','net_targ','ves_serp','ves_clods']; //will load these frim a file
    //console.log(img_avail_features);
    //TODO Need to clean up logic below; for some reason if I reset all the buttons above and then ran the below code, nothing got set
    //Not sure if I was running into a race condition?

    feats_in_cur_image = []

    ///Hmm... the feature list.... hm
    //annotated_feature_list = superpixel_markup_info

    $.each(annotated_feature_list, function(index, value) {
        //console.log(index, value);
        ///This needs to be adapted for the new layout we are using..
       // console.log(value);

        if (img_avail_features.indexOf(value.id) < 0) { //feature is not present
            //the ID of the feature buttons actually have feat_ prepended to the feature name..
            $("#feat_" + value.id).addClass('disabled');
            // $("#feat_net_targ").addClass('disabled');
        } else if (img_avail_features.indexOf(value.id) > -1) {
            $("#feat_" + value.id).removeClass('disabled');
            feats_in_cur_image.push(value.id);
        }
    });

    //I am adding in additional code to also push this list of features into a separate around

    console.log(feats_in_cur_image);
    $("#featbtn_ImageSpecific").empty();
    $("#featbtn_ImageSpecific").text(feats_in_cur_image.join(", "));
    //May want to add stats on counts??


    $(function() {
        //Adding keyboard listnered to toggle the tiles on/off if I press the letter t (for toggle)
        $("body").keypress(function(event) {
            if (event.keyCode == 116) {
                cur_opacity = $('.tileClass').attr('opacity');
                //cur_slider_value = $("#slider").slider("option", "value");
                cur_opacity = 100;
                cur_slider_value = OpacitySlider.val();
                var new_opacity = (cur_opacity == 0) ? cur_slider_value : 0;
                $('.tileClass').attr('opacity', new_opacity);
            }
        });
    });

}

function get_image_data(image_uid) {
    //So becore I can actually load the image itself (i.e. the URL), I need to get the image metadata which contains
    //a lot of various but useful parameters I will eventually need

    //I also need to get the segmentation aka superpixels once I haev grabbed the data..


    $.getJSON('https://isic-archive.com/api/v1/image/' + image_uid, function(data) {
        cur_image_metadata = data;
        //Need to pass the image metadata
        load_new_image_from_api(cur_image_metadata)
            //Now load the superpixel data..
            //console.log("trying to load superpixel data");
        study_id = $("#data_source_dd").val();


        console.log(cur_image_metadata);//Need to get the segmentation data as well....
        get_image_annotation_data(study_id, image_uid);


          get_avail_image_segmentations(image_uid);
        //             hide_unannotated_features(superpixel_markup_info);
        //             //Also add in something to actual  lly display this..
        //             new_mark_superpixels();

    }).fail(function() {
        // alert('You do not have access to this image...');
        //This is currently a simpsons scene
        defaultimg_not_avail = {
            'type': 'legacy-image-pyramid',
            levels: [{
                'url': 'https://c1.staticflickr.com/3/2150/2101058680_64fa63971e.jpg',
                'height': 435,
                'width': 356,
            }]
        }
        $(".boundaryClass").remove();
        dg_viewer.clearOverlays();
        dg_viewer.open(defaultimg_not_avail);;

    });

}

function load_new_image_from_api(image_metadata) {
    //The image metadata is pulled from the API
    //First remove all of the SVG elements to prevent the screen from flashing weird colors
    $(".tileClass").remove();
    //IMPORTANT ISSUE HERE.. OSD NEEDS TO BE PATCHED OR I NEED THE BELOW HACK WHICH HARD CODES THE .JPG... it wasn't figuring this out on its own
    base_url = `https://isic-archive.com/api/v1/image/${image_metadata['_id']}/`;
    image_filename_url = base_url + 'download?contentDisposition=inline&.jpg' //Please note this hack, without the .jpg osd couldn't read

    new_tile_source = {
            'type': 'legacy-image-pyramid',
            levels: [{
                'url': image_filename_url,
                'height': image_metadata.meta.acquisition.pixelsY,
                'width': image_metadata.meta.acquisition.pixelsX,
            }]
        }
        //update_rater_overlays(image_name);  <<TO DOO!!!!
    dg_viewer.open(new_tile_source);

    //Now that the new image is loaded, should next load the actual markup data for this image
    //I should call this function when I select an image...
    //This gets the markup info for the currently selected image
    // $.getJSON('api/TileInfo/ALL/' + image_name, function(data) {
    //     superpixel_markup_info = data;
    //     //I am going to disable buttons on the feature list if that feature isn't present in the currnet image...
    //     hide_unannotated_features(superpixel_markup_info);
    //     //Also add in something to actual  lly display this..
    //     new_mark_superpixels();
    // })

}


function load_rater_list(study_uid) {
    //This will create the buttons for the individual ratesrs
    $("#rater_color_list").empty();

    raters = ['braunr', 'haroldr', 'carrerac', 'marghooa']; //TO REMOVE ONCE I CAN LOAD THESE THINGS
    $.each(raters, function(n, v) {
        //$("#rater_color_list").append(`<li><span style="color:${colours[n]}">${v}</span></li>`);
        $("#rater_color_list").append(
            `<span class="btn btn-default rater_span "><input type='checkbox' class="overlay_toggle" name="${v}" value="${v}" id="show_${v}" class="rater_buttons "><label for="show_${v}" style="color:${colours[n]}">${v}</label></input></span>`);
    });

}



function get_avail_image_segmentations(image_uid)
  {
console.log('should be getting segmentations for'+image_uid)
    //Now query the segmentation API
     
    segmentation_URL =  'https://isic-archive.com/api/v1/' + '/segmentation?imageId='+image_uid;
    console.log(segmentation_URL);
    
    cur_image_segmentations = []

    $.getJSON(segmentation_URL, function(data) {
        cur_image_segmentations = data;
        console.log(cur_image_segmentations);
        //I now need to get and then render the boundary--- for now I'll just render the first one
        get_segmentation_boundaries(cur_image_segmentations);
    })
  
}

function get_segmentation_boundaries( img_segmentation_list)
    {
        console.log('need to get oundaries now');
        console.log(img_segmentation_list);

        //I will just get the first one...
        segmentation_boundaries_URL =  'https://isic-archive.com/api/v1/segmentation/' + img_segmentation_list[0]['_id'];
        
        lesion_boundary_data = [];
        $.getJSON(segmentation_boundaries_URL, function(data) {
                lesion_boundary_data = data;
                console.log(lesion_boundary_data);
                console.log('GOT THE BOUNDARY??');
                //Since for now I am only going to bother rendering a single one, I may as well parse it now..
                console.log(lesion_boundary_data.lesionBoundary);
                //the geometry now contains the info I need to render it...
                lesionboundary_to_svgshape( lesion_boundary_data, dg_viewer.viewport.contentSize.x);


                    //DAMN IT--- these x,y coordinates are taken from the original image, not the cropped image I think
             
        });

    }

function get_segmentation_superpixels( img_segmentation_list)
    {
        console.log('need to get superpixels');
        console.log(img_segmentation_list);

        //I will just get the first one...
        segmentation_boundaries_URL =  'https://isic-archive.com/api/v1/segmentation/' + img_segmentation_list[0]['_id'];
        console.log(img_segmentation_list[0])
        lesion_boundary_data = [];
        $.getJSON(segmentation_boundaries_URL, function(data) {
                lesion_boundary_data = data;
                console.log(lesion_boundary_data);
                console.log('GOT THE BOUNDARY??');
                //Since for now I am only going to bother rendering a single one, I may as well parse it now..
               // console.log(lesion_boundary_data.lesionBoundary);
                //the geometry now contains the info I need to render it...
                lesionboundary_to_svgshape( lesion_boundary_data, dg_viewer.viewport.contentSize.x);


                    //DAMN IT--- these x,y coordinates are taken from the original image, not the cropped image I think
             
        });

    }



