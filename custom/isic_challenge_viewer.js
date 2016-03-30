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
    
    //This generates the pretty multicolor tile image
    // TO DO:  MAY WANT TO READD THE SCALE FACTOR FOR OSD TO THE COORDINATE ARRAY WHICH MEANS I HAVE TO DIVIDE EACH elementsby the iamge width

	my_points = geo_array;
	//console.log(my_points);
	d3_20 = d3.scale.category20();  //Build a color palette of 20 colors from d3
    $.each(my_points, function(k, point_list) {
        col = d3_20( random(20)); //Pick a color at random
        d3.select("#p2_svg_target").append("polygon").attr("points", point_list.geometry.coordinates ).style('fill', col).attr('opacity', 0.2).attr('class', 'tileClass').attr('id', 'tile' + point_list.properties.labelindex);
    });

    //I also need to modify the viewBox of the SVG element based on the image width and height of the current image
	$("#p2_svg_target").removeAttr("viewBox")
    new_viewbox = "0 0 " + img_width + ' ' + img_height;
    d3.select("#p2_svg_target").attr("viewBox",new_viewbox)
    //So this is a bug/feature of SVG and jquery, it inserts the attributes as viewbox NOT viewBox (aka see the spelling)
    //So I am using d3 and not jQuery to modifiy this attributes

    //ALSO NEED TO CHANGE AND UPDATE THE BACKGROUND IMAGE FOR THE SVG
    $("#p2_baseimgsvg").attr('xlink:href',image_info.image_path);
    //Also need to update the width and height of the image container
    $("#p2_baseimgsvg").attr('height',image_info.image_height);
    $("#p2_baseimgsvg").attr('width',image_info.image_width);

}


function show_features(image_id, feature_to_display)
	{
		//Given an image_id, this will display the superpixels that have been marked up for that image

		console.log('need features for'+image_id,feature_to_display);
		$(".tileClass").attr('opacity',0);

		//This is a lame hack, rr gets updated with the latest image I am looking at
		sup_pix_for_feat = rr[feature_to_display];
		//console.log(sup_pix_for_feat);
		$.each(sup_pix_for_feat,function(k,v) { if (v!=0){ $("#tile"+k).attr('opacity',0.8);$("#tile"+k).css('fill','blue') }
	}


			)

	}


// function new_mark_superpixels(sp_info) {
//     $(".tileClass").css('fill', 'none');

//     //need to add in the current_feature
//     if (superpixel_markup_info[current_feature]) {
//         num_superpixels = Object.keys(superpixel_markup_info[current_feature]).length;
//     } else {
//         return;
//     }

//     // console.log(num_superpixels)
//     $("#tile_info_stats").empty(); /// clear the current DIV before I start putting stats in it..
//     //        $("#tile_info_stats").append(num_superpixels.toString() + ' superpixels are in this image');
//     //This code is very sensitive to on load events...
//     $.each(superpixel_markup_info[current_feature], function(tileID, rater_data) {
//         //         ///I am now iteration over each tile in the selected Image...
//         tileAnnotated = false;
//         raters_for_tile = [];

//         //So because of the way we store the data, I need to iterate through each superpixel and determine which rater(s) marked it up.. then color things
//         $.each(rater_data, function(r, v) {
//             if (v != "0.0") {
//                 //                        console.log(r,v,tileID);
//                 tileAnnotated = true;
//                 raters_for_tile.push(r);
//             }
//         });

//         if (tileAnnotated) {
//             //Now that I know the tile has been annotated, I need to render the results
//             //console.log(raters_for_tile, tileID);

//             if (raters_for_tile.length == 1) {
//                 //In this case the tile is colored for the individual rater.... otherwise it's a color palette
//                 //Currently I am going
//                 //var a = fruits.indexOf("Apple");
//                 rater_index = raters.indexOf(raters_for_tile[0]);
//                 // console.log(raters_for_tile,rater_index)

//                 $("#tile" + tileID).css('fill', colours[rater_index]);

//             } else {
//                 $("#tile" + tileID).css('fill', color_heatmap[raters_for_tile.length]);
//             }
//         }

//     });

//     $(".tileClass").hover(function() {
//         //  console.log(this.id);
//         pixnum = (this.id).substring(4);
//         $("#tile_info_stats").empty(); /// clear the current DIV before I start putting stats in it..
//         //              $("#tile_info_stats").append(num_superpixels.toString() + ' superpixels are in this image');
//         $("#tile_info_stats").append("<br>You are hovering on sp: " + this.id);


//         tile_num = this.id.substring(4); //need to turn the tileID which actually is tile234 or similar into only the number part.. so skip the first 4 chars
//         //Determine who marked up this file
//         pix_raters = superpixel_markup_info[current_feature][tile_num];
//         //remember this may contain ALL raters who assessed this feature, so need to make sure there's not a "0.0" there which means that rater
//         //didn't actually mark that specific superpixel with the given feature
//         rft = [];
//         $.each(pix_raters, function(k, v) {
//             if (v != '0.0') {
//                 rft.push(k);
//             }
//         });
//         //console.log(rft);
//         $("#tile_info_stats").append("<br>Raters: " + JSON.stringify(rft));
//     });

// }