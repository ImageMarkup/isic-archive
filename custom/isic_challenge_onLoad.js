function p2_load_osd(imageID, phase) {
    //This is only working for phase 2, although simple switch for phase 1..
    imageInfo = p2_DataView.item(imageID);
    new_tile_source = {
        'type': 'legacy-image-pyramid',
        levels: [{
            'url': imageInfo.image_path+'?.jpg',
            'height': imageInfo.image_height,
            'width': imageInfo.image_width
        }]
    };
    osd_viewer.open(new_tile_source);

    $("#osd_image_stats").empty();
    //Now append in some stats

    $("#osd_image_stats").append("<h3>Current Image: " + imageInfo.imgname + '</h3>');
    $("#osd_image_stats").append("<p>Total Globules: " + imageInfo.globules_count + '</p>');
    $("#osd_image_stats").append("<p>Total Streaks: " + imageInfo.streaks_count + '</p>');
    //Add in a hook to display what image you are looking at, as well as the globules/streaks count...
    isbi_tabbar.tabs('a5').setActive();
    renderOSD_SVG_Tiles(imageInfo);
}

function update_main_img(image_id) {
    /* Going to make this vary based on the phase */
    cur_image = p1_DataView.item(image_id)

    new_img_url = cur_image['image_path'];
    cur_image_name = cur_image['imgname'];
    new_img_overlay = cur_image['overlay_path'];

    $("#cur_image").text("You are viewing " + cur_image_name);
    $("#p1_liv_parent").attr('src', new_img_url);
    $("#p1_liv_segment").attr('src', new_img_overlay);

    //Now create a view with both combined
    $("#p1_liv_combined").css("background", "url(" + new_img_overlay + ")");
    $("#p1_liv_combined").attr('src', new_img_url);
    console.log(new_img_overlay);
    $("#p1_liv_combined_image").attr('src', new_img_url);
    $("#p1_liv_combined_overlay").attr('src', new_img_overlay);
}

function p2_update_main_img(image_id) {
    /* Going to make this vary based on the phase */
    cur_image = p2_DataView.item(image_id)
    new_img_url = cur_image['image_path'];
    cur_image_name = cur_image['imgname'];

    $("#p2_liv_parent").attr('src', new_img_url);
    $("#cur_image_p2").text("You are viewing " + cur_image_name);
    //Now update the SVG IMAGE
    rr = p2_DataView.item(image_id); //Updating global rr variable for debugging, 
    loadSVGTileData(rr)
        //Now create a view with both combined
}
var p1_DataView;
var p2_DataView; //making these public

function p1_load_done() {
    // This callback is executed when phase1 data is loaded
    fi = p1_DataView.first(); //First Item in this phase
    update_main_img(fi);
}


function p2_load_done() {
    // This callback is executed when phase1 data is loaded
    fi = p2_DataView.first(); //First Item in this phase
    p2_update_main_img(fi);
}


function doOnLoad() {
    p1_DataView = new dhtmlXDataView({
        container: "p1_data_container",
        type: 'p1_dataImgOnly',
        pager: {
            container: "paging_here",
            size: 40,
            group: 8
        }

    });
    p1_DataView.load("/uda/ip_load/phase1test_remote.json", "json", p1_load_done);

    p2_DataView = new dhtmlXDataView({
        container: "p2_data_container",
        type: 'p2_dataImgOnly',
        pager: {
            container: "pager_p2",
            size: 40,
            group: 8
        }
    });

    p2_DataView.load("/uda/ip_load/phase2test_remote.json", "json", p2_load_done);
    // Initialize Slider for Phase 1
    opSlider = new dhtmlXSlider({
        parent: "opacitySlider",
        size: 150,
        value: 0.8,
        step: 0.05,
        min: 0,
        max: 1
    });

    opSlider.attachEvent("onChange", function(value) {
        $("#p1_liv_combined_overlay").css('opacity', value);
    });

    p2_opSlider = new dhtmlXSlider({
        parent: "p2_opacitySlider",
        size: 150,
        value: 0.8,
        step: 0.05,
        min: 0,
        max: 1
    });

    p2_opSlider.attachEvent("onChange", function(value) {
        $(".tileClass").css('opacity', value);
    });

    osd_opSlider = new dhtmlXSlider({
        parent: "osd_tile_slider",
        size: 150,
        value: 0.8,
        step: 0.05,
        min: 0,
        max: 1
    });

    osd_opSlider.attachEvent("onChange", function(value) {
        $(".osdTileClass").css('opacity', value);
    });

    configure_osd('osd_container');

    var iconsPath = {
        dhx_skyblue: "imgs",
        dhx_web: "icons_web",
        dhx_terrace: "icons_terrace"
    };
    //Also create an OSD container

    isbi_tabbar = new dhtmlXTabBar({
        parent: "isbi_tabbar",
        skin: 'dhx_skyblue'
    })


    isbi_tabbar.addTab("a1", "Phase 1", null, null, true);
    isbi_tabbar.addTab("a2", "Phase 2");
    isbi_tabbar.addTab("a3", "Phase 3");
    isbi_tabbar.addTab("a4", "Info");
    isbi_tabbar.addTab("a5", "Detailed Image"); //May debate hiding this until an image is clicked?
    isbi_tabbar.addTab("a6", "MultiRater Viewer"); //May debate hiding this until an image is clicked?


    //Above creates the tabs, this actually assigns the tabs to the objects
    isbi_tabbar.tabs("a1").attachObject("tabphase1");
    isbi_tabbar.tabs("a2").attachObject("tabphase2");
    isbi_tabbar.tabs("a3").attachObject("tabphase3");
    isbi_tabbar.tabs("a4").attachObject("tab_info");
    isbi_tabbar.tabs("a5").attachObject("tab_zoomed");


    //Add click handlers for the OSD Visualization buttons //
    $("#btn_osd_globules").click(function() { osd_colorTiles(this.id,this.style) });
    $("#btn_osd_streaks").click(function() { osd_colorTiles(this.id,this.style) });

}

// Views for Phase 1  , some will work for Phase 2 as well
dhtmlx.Type.add(dhtmlXDataView, {
    name: "p1_dataImgOnly",
    height: 'auto',
    template: "#imgname# <img id=#id# onclick=update_main_img(this.id)  height=100 src='#image_path#'> ",
    height: 120
});
dhtmlx.Type.add(dhtmlXDataView, {
    name: "p1_dataImgOverlay",
    height: 'auto',
    template: "#imgname# <img id=#id# onclick=update_main_img(this.id) height=100 style='background:url(#image_path#)' src='#overlay_path#'>",
    height: 120
});

dhtmlx.Type.add(dhtmlXDataView, {
    name: "p2_dataImgOnly",
    height: 'auto',
    template: "#imgname# <img id=#id# onclick=p2_update_main_img(this.id) onDblClick=p2_load_osd(this.id,'phase2') height=100 src='#image_path#' > ",
    height: 120
});

dhtmlx.Type.add(dhtmlXDataView, {
    name: "p2_dataSuperpixelOverlay",
    height: 'auto',
    template: "#imgname# S: #streaks_count# G: #globules_count# <img id=#id# onclick=p2_update_main_img(this.id) height=100 src='#image_path#' onDblClick=p2_load_osd(this.id,'phase2') >",
    height: 140
});

function filter_p2(filter_properties) {
    //This shoule eventually be much smarter, and filter based on what buttons or facets are done
    console.log('You clicked' + filter_properties);
    p2_DataView.filter(); //resets all the filters
    //This filters out any images that don't have any markup data
    p2_DataView.filter(function(obj, value) {
        if (obj.streaks_count > value && obj.globules_count > value) return true;
        return false
    }, 1)
}
