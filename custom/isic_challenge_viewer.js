// 
// Code is to help load and process data and load and manipulate SVG elements corresponding to user markups
function random(range) {
    return Math.floor(Math.random() * range);
}

var my_points; //Making this global for debugging


// function contourdata_to_shape(contours, img_width) {
//     scale_factor = 1;
//     polygon_list = [];

//     //Openseadragon uses the image width for bo the x and y scale factor... probably should rename this pixel factor
//     x_scale_factor = 1.0 / img_width;
//     y_scale_factor = 1.0 / img_width;

//     x_scale_factor = 1;
//     y_scale_factor = 1;


//     $.each(contours, function(index, contour) {
//         coord_info = contour.geometry.coordinates;

//         coord_string = "";
//         $.each(coord_info, function(k, v) {
//             coord_string += `${(v[0]* x_scale_factor ) },${ ( v[1] * y_scale_factor) } `;
//         }); // the |0 made them all integers

//         //polygon_svg_str = `<polygon points="${coord_string}" style="fill: ${colours[ random(9)]}; stroke; purple; stroke-width: 1; opacity: 0.5;" id="tile${contour.properties.labelindex}" class="tileClass" />`;
//         labelindex = contour.properties.labelindex;

//         polygon_list.push({
//             'coords': coord_string,
//             'labelindex': contour.properties.labelindex
//         });
//     });

//     //Need to add the below function to a callback function for above..
//     $(".tileClass").hover(function() {
//         console.log(this.id)
//     });
//     return polygon_list;
// }



var colours = ['purple', 'blue', 'green  ', 'navy', 'green', 'navy', 'blue', 'pink', 'orange', 'yellow', 'lime', 'green', 'blue', 'navy', 'black'];

function loadSVGTileData(svg_json) {
    console.log('need to load svg data for' + svg_json);
    // SVG_file = image_info_list[imageName].superpixel_svg;
    // img_height = image_info_list[imageName].img_height;
    // img_width = image_info_list[imageName].img_width;
    img_height = 1000
    img_width = 1000
    SVG_file = svg_json

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
    //my_points = contourdata_to_shape(new_geodata, img_width);
    //This generates the pretty multicolor tile image
	//	console.log(my_points);
	my_points = geo_array;
	//console.log(my_points);
    $.each(my_points, function(k, point_list) {
        col = colours[ random(9)];

        	//my_points[2].geometry.coordinates.join(' ')  I need to flatten the coords into a string
        //console.log(point_list);
        d3.select("#p2_svg_target").append("polygon").attr("points", point_list.geometry.coordinates ).style('fill', col).attr('opacity', 0.9).attr('class', 'tileClass').attr('id', 'tile' + point_list.properties.labelindex);
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
                rater_index = raters.indexOf(raters_for_tile[0]);
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
        rft = [];
        $.each(pix_raters, function(k, v) {
            if (v != '0.0') {
                rft.push(k);
            }
        });
        //console.log(rft);
        $("#tile_info_stats").append("<br>Raters: " + JSON.stringify(rft));
    });

}