isic.views.ImageViewerWidget = isic.View.extend({
    initialize: function (settings) {
        /* "model" and "el" must be passed as settings */

        this.renderedModelId = null;

        this.listenTo(this.model, 'change:_id', this._fetchTileInfo);
    },

    _fetchTileInfo: function () {
        if (!this.model.id) {
            this.destroyViewer();
            return;
        }

        girder.restRequest({
            type: 'GET',
            path: 'item/' + this.model.id + '/tiles'
        }).done(_.bind(function (resp) {
            this.destroyViewer();

            this.levels = resp.levels;
            this.tileWidth = resp.tileWidth;
            this.tileHeight = resp.tileHeight;
            this.sizeX = resp.sizeX;
            this.sizeY = resp.sizeY;

            this.render();
        }, this));
    },

    _createViewer: function () {
        var params = window.geo.util.pixelCoordinateParams(
            this.$el, this.sizeX, this.sizeY, this.tileWidth, this.tileHeight);

        _.extend(params.map, {
            // TODO: allow rotation? (add actions to interactor and set allowRotation)
            allowRotation: false,
            interactor: window.geo.mapInteractor({
                actions: [{
                    action: window.geo.geo_action.pan,
                    input: 'left',
                    modifiers: {shift: false, ctrl: false},
                    owner: 'geo.mapInteractor',
                    name: 'button pan'
                }, {
                    action: window.geo.geo_action.zoom,
                    input: 'right',
                    modifiers: {shift: false, ctrl: false},
                    owner: 'geo.mapInteractor',
                    name: 'button zoom'
                }, {
                    action: window.geo.geo_action.zoom,
                    input: 'wheel',
                    modifiers: {shift: false, ctrl: false},
                    owner: 'geo.mapInteractor',
                    name: 'wheel zoom'
                }]
            })
        });
        params.map.max += 2;
        this.viewer = window.geo.map(params.map);

        _.extend(params.layer, {
            useCredentials: true,
            url: girder.apiRoot + '/item/' + this.model.id +
                '/tiles/zxy/{z}/{x}/{y}'
        });
        this.imageLayer = this.viewer.createLayer('osm', params.layer);
    },

    render: function () {
        // Do nothing if model is not set
        if (!this.model.id) {
            return this;
        }

        // Ensure tile info is available before rendering
        if (_.isUndefined(this.sizeX)) {
            this._fetchTileInfo();
            return this;
        }

        // Require map element to have a nonzero size
        if (this.$el.innerWidth() === 0 || this.$el.innerHeight() === 0) {
            return this;
        }

        // Do nothing if already rendered for the current model
        if (this.model.id === this.renderedModelId) {
            return this;
        }

        this.renderedModelId = this.model.id;

        this._createViewer();

        return this;
    },

    destroyViewer: function () {
        if (this.viewer) {
            this.viewer.exit();
            this.viewer = null;

            delete this.levels;
            delete this.tileWidth;
            delete this.tileHeight;
            delete this.sizeX;
            delete this.sizeY;

            this.renderedModelId = null;
        }
    },

    destroy: function () {
        this.destroyViewer();

        isic.View.prototype.destroy.call(this);
    }
});

isic.views.OverlayImageViewerWidget = isic.views.ImageViewerWidget.extend({
    State: {
        ABSENT: 0.0,
        POSSIBLE: 0.5,
        DEFINITE: 1.0
    },

    _createViewer: function () {
        isic.views.ImageViewerWidget.prototype._createViewer.call(this);

        this.annotationLayer = this.viewer.createLayer('feature', {
            features: ['pixelmap']
        });
        this.pixelmap = this.annotationLayer.createFeature('pixelmap', {
            selectionAPI: true,
            url: girder.apiRoot + '/image/' + this.model.id + '/superpixels',
            position: {
                ul: {x: 0, y: 0},
                lr: {x: this.sizeX, y: this.sizeY}
            },
            color: _.bind(function (dataValue, index) {
                var color = {r: 0, g: 0, b: 0, a: 0};
                var shownAlpha = 0.4;

                if (dataValue === this.State.ABSENT) {
                    // This could be semi-transparent, to show "definite negative" tiles
                    color.a = 0.0;
                } else if (dataValue === this.State.POSSIBLE) {
                    color = window.geo.util.convertColor('#fafa00');
                    color.a = shownAlpha;
                } else if (dataValue === this.State.DEFINITE) {
                    color = window.geo.util.convertColor('#0000ff');
                    color.a = shownAlpha;
                }
                // TODO: else, log error
                return color;
            }, this)
        });
        this.annotationLayer.draw();
        this.clear();
    },

    /**
     * Remove all displayed overlays.
     */
    clear: function () {
        this.pixelmap.data([]);
        this.pixelmap.visible(false);
        this.pixelmap.draw();

        this.pixelmap.geoOff();
    },

    /**
     * Display a single view-only feature on the viewer.
     */
    overlay: function (featureValues) {
        this.clear();

        this.pixelmap.data(featureValues);
        this.pixelmap.visible(true);
        this.pixelmap.draw();
    }
});
