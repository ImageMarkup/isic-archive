isic.views.ImageViewerWidget = isic.View.extend({
    initialize: function (settings) {
        /* "model" and "el" must be passed as settings */
        girder.restRequest({
            type: 'GET',
            path: 'item/' + this.model.id + '/tiles'
        }).done(_.bind(function (resp) {
            this.levels = resp.levels;
            this.tileWidth = resp.tileWidth;
            this.tileHeight = resp.tileHeight;
            this.sizeX = resp.sizeX;
            this.sizeY = resp.sizeY;
            this.render();
        }, this));
    },

    render: function () {
        var w = this.sizeX,
            h = this.sizeY,
            mapW = this.$el.innerWidth(),
            mapH = this.$el.innerHeight();

        var minLevel = Math.min(0, Math.floor(Math.log(Math.min(
            (mapW || this.tileWidth) / this.tileWidth,
            (mapH || this.tileHeight) / this.tileHeight)) / Math.log(2)));
        var maxLevel = Math.ceil(Math.log(Math.max(
            w / this.tileWidth,
            h / this.tileHeight)) / Math.log(2));
        this.viewer = window.geo.map({
            node: this.$el,
            // Projection
            gcs: '+proj=longlat +axis=enu',
            ingcs: '+proj=longlat +axis=esu',
            unitsPerPixel: Math.pow(2, maxLevel),
            maxBounds: {
                left: 0,
                top: 0,
                right: w,
                bottom: h
            },
            // Initial view
            zoom: 0,
            center: {
                x: w / 2,
                y: h / 2
            },
            // Navigation
            // TODO: this is a hack to keep scroll bars from appearing?,
            //   and breaks after resize
            width: mapW - 5,
            height: mapH - 5,
            min: minLevel,
            max: maxLevel + 2,
            // TODO: allow rotation? (add actions to interactor and set allowRotation)
            allowRotation: false,
            // TODO: clampBoundsX seems to cause jarring camera behavior after
            //   zoom or move momentum settles, even if it's false
            clampBoundsX: true,
            clampBoundsY: true,
            clampZoom: true,
            interactor: window.geo.mapInteractor({
                actions: [{
                    action: window.geo.geo_action.pan,
                    name: 'click_pan',
                    input: 'left',
                    modifiers: {shift: false, ctrl: false}
                }, {
                    action: window.geo.geo_action.zoom,
                    name: 'click_zoom',
                    input: 'right',
                    modifiers: {shift: false, ctrl: false}
                }, {
                    action: window.geo.geo_action.zoom,
                    name: 'wheel_zoom',
                    input: 'wheel',
                    modifiers: {shift: false, ctrl: false}
                }]
            })
        });

        this.imageLayer = this.viewer.createLayer('osm', {
            useCredentials: true,
            url: girder.apiRoot + '/item/' + this.model.id +
                '/tiles/zxy/{z}/{x}/{y}',
            maxLevel: maxLevel,
            wrapX: false,
            wrapY: false,
            tileOffset: function () {
                return {x: 0, y: 0};
            },
            attribution: '',
            tileWidth: this.tileWidth,
            tileHeight: this.tileHeight,
            tileRounding: Math.ceil,
            tilesAtZoom: _.bind(function (level) {
                var scale = Math.pow(2, maxLevel - level);
                return {
                    x: Math.ceil(this.sizeX / this.tileWidth / scale),
                    y: Math.ceil(this.sizeY / this.tileHeight / scale)
                };
            }, this),
            tilesMaxBounds: _.bind(function (level) {
                var scale = Math.pow(2, maxLevel - level);
                return {
                    x: Math.floor(this.sizeX / scale),
                    y: Math.floor(this.sizeY / scale)
                };
            }, this)
        });

        return this;
    },

    destroy: function () {
        if (this.viewer) {
            this.viewer.exit();
            this.viewer = null;
        }
        isic.View.prototype.destroy.call(this);
    }

});
