/*global _, girder*/

var thumbnailView = {
    views: {}
};

thumbnailView.views.ThumbnailWidget = girder.View.extend({
    initialize: function (settings) {
        'use strict';
        this.item = settings.item;
        this.accessLevel = settings.accessLevel;
        this.item.on('change', function () {
            this.render();
        }, this);
        this.render();
    },

    render: function () {
        'use strict';
        console.log('init thumbnail');

        var meta = this.item.get('meta');

//        if (this.accessLevel >= girder.AccessType.READ && meta && meta.vega) {
        if (this.accessLevel >= girder.AccessType.READ) {
            $(".g-item-info").after(jade.templates.thumbnail());

            $('#thumbnail-img').attr("src", "/api/v1/image/" + this.item.get("_id") + "/thumbnail");

//            $.ajax({
//                url: "/api/v1/item/" + this.item.get("_id") + "/download",
//                type: "GET",
//                dataType: "json",
//                success: function (spec) {
//                    vg.parse.spec(spec, function (chart) {
//                        chart({
//                            el: ".g-item-vega-vis",
//                            renderer: "svg"
//                        }).update();
//                    });
//                }
//            });

        } else {
            $(".g-item-thumbnail")
                .remove();
        }
    }
});


girder.wrap(girder.views.ItemView, 'render', function (render) {
    'use strict';
    this.model.getAccessLevel(_.bind(function (accessLevel) {
        // Because the passthrough call to render() also does an async call to
        // getAccessLevel(), wait until this one completes before invoking that
        // one.
        //
        // Furthermore, we need to call this *first*, because of how the Vega
        // view inserts itself into the app-body-container, which doesn't seem
        // to exist until the passthrough call is made.
        render.call(this);

        this.thumbnailWidget = new thumbnailView.views.ThumbnailWidget({
            item: this.model,
            accessLevel: accessLevel,
            girder: girder
        });

    }, this));

    return this;
});
