import _ from 'underscore';

import geo from 'geojs';

import {getApiRoot, restRequest} from 'girder/rest';

import View from '../../view';

import './imageViewerWidget.styl';

const ImageViewerWidget = View.extend({
    /**
     * @param {ImageModel} settings.model
     * @param {HTMLElement} settings.el - The HTML element to attach to, which must be set upon instantiation.
     */
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

        restRequest({
            url: `image/${this.model.id}/tiles`
        }).done((resp) => {
            this.destroyViewer();

            this.levels = resp.levels;
            this.tileWidth = resp.tileWidth;
            this.tileHeight = resp.tileHeight;
            this.sizeX = resp.sizeX;
            this.sizeY = resp.sizeY;

            this.render();
        });
    },

    _createViewer: function () {
        let params = geo.util.pixelCoordinateParams(
            this.$el, this.sizeX, this.sizeY, this.tileWidth, this.tileHeight);

        _.extend(params.map, {
            // TODO: allow rotation? (add actions to interactor and set allowRotation)
            allowRotation: false,
            interactor: geo.mapInteractor({
                actions: [{
                    action: geo.geo_action.pan,
                    input: 'left',
                    modifiers: {shift: false, ctrl: false},
                    owner: 'geo.mapInteractor',
                    name: 'button pan'
                }, {
                    action: geo.geo_action.zoom,
                    input: 'right',
                    modifiers: {shift: false, ctrl: false},
                    owner: 'geo.mapInteractor',
                    name: 'button zoom'
                }, {
                    action: geo.geo_action.zoom,
                    input: 'wheel',
                    modifiers: {shift: false, ctrl: false},
                    owner: 'geo.mapInteractor',
                    name: 'wheel zoom'
                }],
                keyboard: {
                    actions: {},
                    meta: {},
                    focusHighlight: false
                }
            })
        });
        params.map.max += 2;
        this.viewer = geo.map(params.map);

        _.extend(params.layer, {
            useCredentials: true,
            url: `${getApiRoot()}/image/${this.model.id}/tiles/{z}/{x}/{y}`
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

        View.prototype.destroy.call(this);
    }
});

export default ImageViewerWidget;
