
var Pixelmap = function (containerDiv) {
    /* Create a pixelmap, given a jQuery-wrapped <div> for the container. */
    this.container = containerDiv;

    this.activeState = Pixelmap.State.DEFINITE;

    this.map = null;
    this.imageLayer = null;
    this.annotationLayer = null;
    this.pixelmap = null;
};

Pixelmap.State = {
    ABSENT: 0.0,
    POSSIBLE: 0.5,
    DEFINITE: 1.0
};

Pixelmap.prototype.reset = function () {
    /* Remove the active image, in preparation for another image to be loaded. */

};

Pixelmap.prototype.loadImage = function (imageId) {
    /* Load an image for display or annotation use. */
    var loaded = $.Deferred();

    // TODO: authenticate this Ajax call
    $.ajax({
        url: '/api/v1/item/' + imageId + '/tiles'
    }).done(_.bind(function (resp) {
        var w = resp.sizeX,
            h = resp.sizeY,
            mapW = this.container.innerWidth(),
            mapH = this.container.innerHeight();

        var minLevel = Math.min(0, Math.floor(Math.log(Math.min(
            (mapW || resp.tileWidth) / resp.tileWidth,
            (mapH || resp.tileHeight) / resp.tileHeight)) / Math.log(2)));
        var maxLevel = Math.ceil(Math.log(Math.max(
            w / resp.tileWidth,
            h / resp.tileHeight)) / Math.log(2));
        this.map = window.geo.map({
            node: this.container,
            ingcs: '+proj=longlat +axis=esu',
            gcs: '+proj=longlat +axis=enu',
            maxBounds: {
                left: 0,
                top: 0,
                right: w,
                bottom: h
            },
            center: {
                x: w / 2,
                y: h / 2
            },
            min: minLevel,
            max: maxLevel,
            allowRotation: false,
            clampBoundsX: true,
            clampBoundsY: true,
            zoom: 0,
            unitsPerPixel: Math.pow(2, maxLevel),
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
        // TODO: allow rotation? (add actions to interactor and set allowRotation)

        this.imageLayer = this.map.createLayer('osm', {
            useCredentials: true,
            url: '/api/v1/item/' + imageId + '/tiles/zxy/{z}/{x}/{y}',
            maxLevel: maxLevel,
            wrapX: false,
            wrapY: false,
            tileOffset: function () {
                return {x: 0, y: 0};
            },
            attribution: '',
            tileWidth: resp.tileWidth,
            tileHeight: resp.tileHeight,
            tileRounding: Math.ceil,
            tilesAtZoom: function (level) {
                var scale = Math.pow(2, maxLevel - level);
                return {
                    x: Math.ceil(resp.sizeX / resp.tileWidth / scale),
                    y: Math.ceil(resp.sizeY / resp.tileHeight / scale)
                };
            },
            tilesMaxBounds: function (level) {
                var scale = Math.pow(2, maxLevel - level);
                return {
                    x: Math.floor(resp.sizeX / scale),
                    y: Math.floor(resp.sizeY / scale)
                };
            }
        });

        this.annotationLayer = this.map.createLayer('feature', {
            features: ['pixelmap']
        });
        this.pixelmap = this.annotationLayer.createFeature('pixelmap', {
            selectionAPI: true,
            url: '/api/v1/image/' + imageId + '/superpixels',
            position: {
                ul: {x: 0, y: 0},
                lr: {x: w, y: h}
            },
            mapColor: function (dataValue, index) {
                var color = {r: 0, g: 0, b: 0, a: 0};
                var shownAlpha = 0.4;

                if (dataValue === Pixelmap.State.ABSENT) {
                    // This could be semi-transparent, to show "definite negative" tiles
                    color.a = 0.0;
                } else if (dataValue === Pixelmap.State.POSSIBLE) {
                    color = window.geo.util.convertColor('#fafa00');
                    color.a = shownAlpha;
                } else if (dataValue === Pixelmap.State.DEFINITE) {
                    color = window.geo.util.convertColor('#0000ff');
                    color.a = shownAlpha;
                }
                // TODO: else, log error
                return color;
            }
        });
        this.annotationLayer.draw();

        this.clear();

        // TODO: This has to come after .clear, since that calls .geoOff, calling
        // .clear before this resolves will still break things
        this.pixelmap.geoOn(window.geo.event.pixelmap.prepared, function (evt) {
            loaded.resolve();
        });
    }, this));

    return loaded.promise();
};

Pixelmap.prototype.clear = function () {
    /* Remove all active or displayed overlays. */
    this.pixelmap.data([]);
    this.pixelmap.visible(false);
    this.pixelmap.draw();

    this.pixelmap.geoOff();

    var interactor = this.map.interactor();
    // TODO: change this to add and remove actions
    interactor.hasAction(undefined, 'click_pan').input = {left: true};
    interactor.hasAction(undefined, 'click_zoom').input = {right: true};
};

Pixelmap.prototype._throttledPixelmapDraw = _.throttle(function () {
    this.pixelmap.draw();
}, 100);
Pixelmap.prototype._setSuperpixel = function (index, value) {
    var data = this.pixelmap.data();
    if (!data) {
        // TODO: this should never happen, remove once features can be cleard
        return;
    }
    if (data[index] !== value) {
        data[index] = value;
        this.pixelmap.data(data);
        this.pixelmap.draw();
        // this._throttledPixelmapDraw();
    }
};
Pixelmap.prototype.activate = function (featureValues) {
    /* Enable drawing on the map, with an optional set of values to pre-fill. */
    this.clear();

    var interactor = this.map.interactor();
    // TODO: change this to add and remove actions
    interactor.hasAction(undefined, 'click_zoom').input = {middle: true};
    interactor.hasAction(undefined, 'click_pan').input = {right: true};

    this.pixelmap.geoOn(window.geo.event.feature.mousemove, _.bind(function (evt) {
        if (evt.mouse.buttons.left) {
            if (evt.mouse.modifiers.shift) {
                this._setSuperpixel(evt.index, Pixelmap.State.ABSENT);
            } else {
                this._setSuperpixel(evt.index, this.activeState);
            }
        }
    }, this));
    this.pixelmap.geoOn(window.geo.event.feature.mouseclick, _.bind(function (evt) {
        if (evt.mouse.buttonsDown.left) {
            if (evt.mouse.modifiers.shift) {
                this._setSuperpixel(evt.index, Pixelmap.State.ABSENT);
            } else {
                this._setSuperpixel(evt.index, this.activeState);
            }
        }
    }, this));

    if (featureValues === undefined) {
        featureValues = new Array(this.pixelmap.maxIndex());
        for (var i = 0, len = featureValues.length; i < len; ++i) {
            featureValues[i] = Pixelmap.State.ABSENT;
        }
    }

    this.pixelmap.data(featureValues);
    this.pixelmap.visible(true);
    this.pixelmap.draw();
};

Pixelmap.prototype.setActiveState = function (stateValue) {
    /* Set the value that clicked superpixels will be filled with when drawing */
    if (stateValue !== Pixelmap.State.POSSIBLE &&
        stateValue !== Pixelmap.State.DEFINITE) {
        // TODO: log error
        return;
    }
    this.activeState = stateValue;
};

Pixelmap.prototype.getActiveValues = function () {
    /* Return an array representing the current user-drawn values. */
    return this.pixelmap.data();
};

Pixelmap.prototype.display = function (featureValues) {
    /* Display a view-only feature on the map. */
    this.clear();

    if (featureValues === undefined) {
        // TODO: this should just be a mandatory parameter
        featureValues = [];
    }

    this.pixelmap.data(featureValues);
    this.pixelmap.visible(true);
    this.pixelmap.draw();
};
