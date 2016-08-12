//Putting Various Helper functions up here
var color20 = d3.scale.category20();
var avail_studies;
var flt = {};

var colours = ['purple', 'blue', 'green  ', 'navy', 'green', 'navy', 'blue', 'pink', 'orange', 'yellow', 'lime', 'green', 'blue', 'navy', 'black'];
var color_heatmap = ['blue', 'blue', 'yellow', 'orange', 'red'];


var image_info_list = {};
var superpixel_markup_info = {}; //Stores the marked up data for each tile and rater
var active_image = '';
var current_feature = "net_typ";
var avail_studies_dict = {};
var annotated_feature_list = [];

//feature group should not have a space... need to think about this

var feature_groups = [{
    'feature_group': 'Structures',
    'feature_abbrev': 'str'
}, {
    'feature_group': 'Colors',
    'feature_abbrev': 'c'
}, {
    'feature_group': 'Vessels',
    'feature_abbrev': 'ves'
}, {
    'feature_group': 'Other',
    'feature_abbrev': 'oth'
}, {
    'feature_group': 'Network',
    'feature_abbrev': 'net'
}, {
    'feature_group': 'ImageSpecific',
    'feature_abbrev': 'THISSTRINGWILLNEVERMATCH'

}];

var new_geodata;
var my_data = {};

var dg_viewer;

var OpacitySlider;
var study_url = 'https://isic-archive.com/api/v1/study';

$(document).ready(function() {



 dg_viewer = OpenSeadragon({
    id: "openseadragon1",
    prefixUrl: "/static/built/plugins/isic_archive/extra/bower_components/openseadragon/built-openseadragon/openseadragon/images/",
    showNavigator: true
});

svg_layer = dg_viewer.svgOverlay(); //need to move to onload handler

    //Opacity slides which is at the top of the toolbar for  changing opacity..
    OpacitySlider = $('#opacity_slider').bootstrapSlider({}); //I can set these options at run time
    OpacitySlider.change(function(val) {
        new_slider_value = val.value.newValue;
        console.log('new slider value is' + new_slider_value);
        $(".tileClass").attr('opacity', new_slider_value);
    });
    //TODO:  Should be able to set the change function in the slider constructor.. not sure of the syntax


    avail_studies = load_avail_studies(); //This requires no parameters and populates the data_source_dd selection box

    $("#data_source_dd").change(function(data) {
        //I now should actually load the images associated with this data set...
        //Now pull the image list for this data source and then update the image_list_dd
        study_uid = this.value;

        uda2pilot_demo = '55c4668a9fc3c1536a0130c8';
        study_uid = uda2pilot_demo;

        load_image_list(study_uid);
        load_feature_list(study_uid); //This will populate the feature widget..
        load_rater_list(study_uid); //I think this is another endpoint...
    });

    //Need to add in the button actions for the filter clicks

    $("#filter_dialog").dialog({
        autoOpen: false,
        width: 'auto'
    });
    $("#show_magic").click(function() {
        $("#filter_dialog").dialog('open');
        return false;
    });
    $("#filter_dialog").html(color_filter_html);

    $(":checkbox").prop('checked', true); //reset all checkboxes to be checked...
    $('.overlay_toggle').click(function() {
        color_some_tiles(this.id, "thefeatureIwanttolookat");
    });

    // Add event handler for changing the image

    $("#image_list_dd").change(function() {
        //##This needs to clear as well as update information and change the viewer
        //Need to change the image source based on the new image I just added in the toggle, will also push the text
        // to a DIV so it's obvious what Image I am looking at
        //console.log(image_info_list[this.value].filename_url);
        //ALSO ADD IN SOMETHING HERE TO CHANGE THE OVERLAY images
        image_uid = this.value;
        //Need to make this information global somehow...
        get_image_data(image_uid);
    });

    $("#tile_toggle").button().click(function() {
        console.log(this.id + 'was pressed')
        $(".tileClass").css('fill', 'none')
    });

    $("#tile_button").click(function() {
        //Make sure tiles are actually visible in case they were toggled off..
        cur_slider_value = OpacitySlider.val();
        $('.tileClass').attr('opacity', cur_slider_value);
        show_all_tiles();
    });

    //Adding RADIO Buttons to allow me to select features
    show_all_tiles();
    new_mark_superpixels();

    $(function() {
        $('[data-toggle="tooltip"]').tooltip()
    })

    $("#image_list_dd").select2({'width':200});
    //end of READY function

    //Load the feature set... so this is based on the data that's stores in avail_studies; may want to consider making this a dict
    $.each(avail_studies, function(idx, val) {
        console.log(val.meta.featuresetId);
        console.log('load this feature set??');
        //need to see if this matches the currently selected data set?
        cur_image_set_id = $("#image_list_dd").val();
        console.log(cur_image_set_id);
    });


});


$('#tile_img').toggle();
//$(".rater_span").css('background-color','black')


function update_rater_overlays(imageName) {
    //console.log("NEED TO update the overlay SRC ids as well" + imageName);
    //This will eventually need to reed the list or raters and update the sources for all of the raters that have been added
    //ALSO need to add in something that populates the stats for the rater(s)
    loadSVGTileData(imageName);
    //NEED TO GRAB THE OVERLAY FOR THIS IMAGE
    $(":checkbox").prop('checked', true); //reset all checkboxes to be checked...
    new_mark_superpixels();
}

//COME HERE LATER--- ADD SOME FUNCTION THAT RUNS ON DOCUMENT COMPLETION THAT LOADS THE IMAGE FOR THE VIEWER AND
//THE PROPER OVERLAY

//need to add a callback function to this as well... hmm so want to load the geodata than push it to the SVG
//<!-- Some tips on working with SVG docs http://stackoverflow.com/questions/3642035/jquerys-append-not-working-with-svg-element
//ttps://www.dashingd3js.com/creating-svg-elements-based-on-data dg_viewer.viewport.maxZoomPixelRatio=5 dg_viewer.viewport.minZoomPixelRatio=0.4 Can play //around with these $(".rater_buttons").click( function() { console.log(this.id) }); -->
