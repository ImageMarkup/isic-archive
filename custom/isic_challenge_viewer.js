// 
// Code is to help load and process data and load and manipulate SVG elements corresponding to user markups
function random(range) {
    return Math.floor(Math.random() * range);
}
var my_points; //Making this global for debugging


function getCookie(cname) {
    var name = cname + "=";
    var ca = document.cookie.split(';');
    for (var i = 0; i < ca.length; i++) {
        var c = ca[i];
        while (c.charAt(0) == ' ') c = c.substring(1);
        if (c.indexOf(name) == 0) return c.substring(name.length, c.length);
    }
    return "";
}



$.ajax({
        url: "/api/v1/dataset",
        headers: { 'Girder-Token': getCookie('girderToken') },

    })
    .done(function(data) {
        if (console && console.log) {
            console.log("Sample of data:", data);
        }
    });



function osd_colorTiles(feature_to_display, style) {
    //Given the feature to display, this will update the SVG OSD image
    console.log("should be rendering feature", feature_to_display);

    $(".osdTileClass").attr('opacity', 0); //make all tiles 0

    feat = feature_to_display.replace('btn_osd_','');

    btn_color = style['background-color'];
    //     //This is a lame hack, rr gets updated with the latest image I am looking at
    sup_pix_for_feat = rr[feat];
    //     //console.log(sup_pix_for_feat);
    $.each(sup_pix_for_feat, function(k, v) {
        if (v != 0) {
            $("#osdtile" + k).attr('opacity', 0.8);
            $("#osdtile" + k).css('fill', btn_color)
        }
    })


}




function loadSVGTileData(image_info) {
    SVG_file = image_info.svgjson_file; //This contains a JSONified list of boundary coordinates for each polygon in the superpixe
    img_height = image_info.image_height;
    img_width = image_info.image_width;

    $.getJSON(SVG_file).done(
        function(result) {
            geo_array = [];
            $.each(result, function(i, contour) { geo_array.push(JSON.parse(contour)) })

            update_SVG_layer(geo_array, image_info); //Now that I have an array of polygons from the SVGJSON file, I can load them
        })
}

function update_SVG_layer(SVG_json, image_info) {
    // This will update the current phase 2 image with an SVG containing the image boundaries...

    //Delete all the current tiles, since I am going to replace them
    $(".tileClass").remove();
    //SVG_json is a list of contours, technically an array of contours, i.e. the points I need to render to make the shape

    curOpacity = p2_opSlider.getValue();
    d3_20 = d3.scale.category20(); //Build a color palette of 20 colors from d3
    $.each(SVG_json, function(k, point_list) {
        col = d3_20(random(20)); //Pick a color at random
        d3.select("#p2_svg_target").append("polygon").attr("points", point_list.geometry.coordinates).style('fill', col).attr('opacity', curOpacity).attr('class', 'tileClass').attr('id', 'tile' + point_list.properties.labelindex);
    });

    //I also need to modify the viewBox of the SVG element based on the image width and height of the current image
    $("#p2_svg_target").removeAttr("viewBox")
    new_viewbox = "0 0 " + img_width + ' ' + img_height;
    d3.select("#p2_svg_target").attr("viewBox", new_viewbox)
        //So this is a bug/feature of SVG and jquery, it inserts the attributes as viewbox NOT viewBox (aka see the spelling)
        //So I am using d3 and not jQuery to modifiy this attributes

    //ALSO NEED TO CHANGE AND UPDATE THE BACKGROUND IMAGE FOR THE SVG
    $("#p2_baseimgsvg").attr('xlink:href', image_info.image_path);
    //Also need to update the width and height of the image container
    $("#p2_baseimgsvg").attr('height', image_info.image_height);
    $("#p2_baseimgsvg").attr('width', image_info.image_width);
}


function show_features(image_id, feature_to_display, style) {
    //Given an image_id, this will display the superpixels that have been marked up for that image
    $(".tileClass").attr('opacity', 0);
    btn_color = style['background-color'];
    //This is a lame hack, rr gets updated with the latest image I am looking at
    sup_pix_for_feat = rr[feature_to_display];
    //console.log(sup_pix_for_feat);
    $.each(sup_pix_for_feat, function(k, v) {
        if (v != 0) {
            $("#tile" + k).attr('opacity', 0.8);
            $("#tile" + k).css('fill', btn_color)
        }
    })
}

var osd_viewer; //Makign this publically scoped for debugging...

function configure_osd(container_to_use) {
    //Given a target container, this will instantiate an openseadragon viewer
    osd_viewer = OpenSeadragon({
        'id': container_to_use,
        'prefixUrl': '/static/built/plugins/isic_archive/extra/bower_components/openseadragon/built-openseadragon/openseadragon/images/',
        'navigationPosition': 'UPPER_RIGHT',
        'showNavigation': true,
        'maxZoomLevel': 4,
        'showRotationControl': true, // Show rotation buttons
    })

    defaultimg_not_avail = {
        'type': 'legacy-image-pyramid',
        levels: [{
            'url': 'https://c1.staticflickr.com/3/2150/2101058680_64fa63971e.jpg',
            'height': 435,
            'width': 356,
        }]
    };

    osd_viewer.open(defaultimg_not_avail);
    //Will now bind an SVG object to the viewer so I can do fun D3 stuff
    osd_svg_layer = osd_viewer.svgOverlay();

}


function renderOSD_SVG_Tiles(image_info) {
    //This is a bit annoying, but I have to reformat the SVGJSON file to make it compatible with Openseadragon
    //so instead of using integers, I have to divid everything by the image_width, but since I am storing
    //the coordinates as strings, I have to do a lot of very non-intuitive text parsing to do this.. 
    //May try and reformat the incoming SVGJSON file to just return everything as an array, as flattening
    //an array is a lot easier to read than converting a string to an array back to a string

    $(".osdTileClass").remove();
    $.getJSON(rr.svgjson_file).done(function(contour_array) {
        //Irritatingly, the returned data is a string, not a JSON file, not sure why I am doing this wrong
        wid = image_info.image_width;
        //Now iterate through the countours
        $.each(contour_array, function(idx, row) {

            cntr = JSON.parse(row);
            unscaled_coords = cntr.geometry.coordinates.trim().split(" ");
            //Convert this temporarily to an xy array, and then convert it back..
            unscaled_xy_array = [];
            $.each(unscaled_coords, function(idx2, row2) {
                dt = row2.split(',');
                unscaled_xy_array.push({ 'x': dt[0] / wid, 'y': dt[1] / wid })
            })
            flattened_string = "";
            $.each(unscaled_xy_array, function(idx3, xy) { flattened_string += ' ' + xy.x + ',' + xy.y })
                //Now I can actually push this to d3
            //    console.log(cntr);
            d3.select(osd_svg_layer.node()).append("polygon").attr('points', flattened_string).style('fill', 'blue').attr('opacity', 0.5).attr('class', 'osdTileClass').attr('id', 'osdtile' + cntr.properties.labelindex);
        })
    });

}
