
var Pixelmap = function (containerDiv) {
    /* Create a pixelmap, given a jQuery-wrapped <div> for the container. */
    this.container = containerDiv;

    this.activeState = Pixelmap.State.DEFINITE;

    this.viewer = null;
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

    // TODO: do Ajax via Backbone or Angular
    function getCookie(cname) {
        var name = cname + '=';
        var ca = document.cookie.split(';');
        for (var i = 0; i < ca.length; i++) {
            var c = ca[i];
            while (c.charAt(0) === ' ') {
                c = c.substring(1);
            }
            if (c.indexOf(name) === 0) {
                return c.substring(name.length, c.length);
            }
        }
        return '';
    }
    $.ajax({
        url: '/api/v1/item/' + imageId + '/tiles',
        headers: {'Girder-Token': getCookie('girderToken')}
    }).done(_.bind(function (resp) {
        // work around a GeoJS sizing bug
        this.container.css('font-size', '0');

        var params = window.geo.util.pixelCoordinateParams(
            this.container, resp.sizeX, resp.sizeY, resp.tileWidth, resp.tileHeight);

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
        params.map.unitsPerPixel = Math.pow(2, params.map.max);
        params.map.max += 2;
        this.viewer = window.geo.map(params.map);

        _.extend(params.layer, {
            useCredentials: true,
            url: '/api/v1/item/' + imageId + '/tiles/zxy/{z}/{x}/{y}'
        });
        this.imageLayer = this.viewer.createLayer('osm', params.layer);

        this.annotationLayer = this.viewer.createLayer('feature', {
            features: ['pixelmap']
        });
        this.pixelmap = this.annotationLayer.createFeature('pixelmap', {
            selectionAPI: true,
            url: '/api/v1/image/' + imageId + '/superpixels',
            position: {
                ul: {x: 0, y: 0},
                lr: {x: resp.sizeX, y: resp.sizeY}
            },
            color: function (dataValue, index) {
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

    var interactor = this.viewer.interactor();
    // TODO: change this to add and remove actions
    interactor.hasAction(undefined, 'button pan').input = {left: true};
    interactor.hasAction(undefined, 'button zoom').input = {right: true};
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
        // TODO: do we ever want to throttle?
        // this._throttledPixelmapDraw();
    }
};
Pixelmap.prototype.activate = function (featureValues) {
    /* Enable drawing on the map, with an optional set of values to pre-fill. */
    this.clear();

    var interactor = this.viewer.interactor();
    // TODO: change this to add and remove actions
    interactor.hasAction(undefined, 'button zoom').input = {middle: true};
    interactor.hasAction(undefined, 'button pan').input = {right: true};

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
        featureValues = new Array(this.pixelmap.maxIndex() + 1);
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
