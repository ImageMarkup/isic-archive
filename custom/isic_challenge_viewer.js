// 
// Code is to help load and process data and load and manipulate SVG elements corresponding to user markups
function random(range) {
    return Math.floor(Math.random() * range);
}

var my_points; //Making this global for debugging



function loadSVGTileData(image_info) {
    SVG_file = image_info.svgjson_file;
    img_height = image_info.image_height;
    img_width = image_info.image_width;
    /* TO DO:  Fix this ugly mess of a load function */
    // new_geodata = function() {
    //     console.log('loading new geo data');
    //     geo_array = [];
    //     $.ajax({
    //         'async': false,
    //         'global': false,
    //         'url': SVG_file,
    //         'dataType': "json",
    //         'success': 
    //             //GEO ARRAY IS NOW generated with contours... so can call another function to generate an SVG layer a well //
    //         }
    //     });

    //     return geo_array;
    // }();
    $.getJSON(SVG_file).done(
        function(result) {
            geo_array = []
            $.each(result, function(i, contour) { geo_array.push(JSON.parse(contour))})
            update_SVG_layer(geo_array,image_info); //Now that I have an array of polygons from the SVGJSON file, I can load them
        })
}



function update_SVG_layer(SVG_json_file,image_info) {
    // This will update the current phase 2 image with an SVG containing the image boundaries...

    //Delete all the current tiles, since I am going to replace them
    $(".tileClass").remove();


    my_points = SVG_json_file;
    //console.log(my_points);
    d3_20 = d3.scale.category20(); //Build a color palette of 20 colors from d3
    $.each(my_points, function(k, point_list) {
        col = d3_20(random(20)); //Pick a color at random
        d3.select("#p2_svg_target").append("polygon").attr("points", point_list.geometry.coordinates).style('fill', col).attr('opacity', 0.2).attr('class', 'tileClass').attr('id', 'tile' + point_list.properties.labelindex);
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
        }


    )

}
