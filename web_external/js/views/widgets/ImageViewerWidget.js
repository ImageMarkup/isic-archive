isic.views.ImageViewerWidget = isic.View.extend({
    initialize: function (settings) {
        /* "model" and "el" must be passed as settings */

        this.renderedModelId = null;

        this.listenTo(this.model, 'change', this.fetchTileInfo);
    },

    fetchTileInfo: function () {
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

    render: function () {
        // Do nothing if model is not set
        if (!this.model.id) {
            return this;
        }

        // Ensure tile info is available before rendering
        if (_.isUndefined(this.sizeX)) {
            this.fetchTileInfo();
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

        // work around a GeoJS sizing bug
        this.$el.css('font-size', '0');

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
        // setting unitsPerPixel fixes a bug in pixelCoordinateParams
        params.map.unitsPerPixel = Math.pow(2, params.map.max);
        params.map.max += 2;
        this.viewer = window.geo.map(params.map);

        _.extend(params.layer, {
            useCredentials: true,
            url: girder.apiRoot + '/item/' + this.model.id +
                '/tiles/zxy/{z}/{x}/{y}'
        });
        this.imageLayer = this.viewer.createLayer('osm', params.layer);

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
