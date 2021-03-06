<template lang="pug">
  div(ref='pixelmap')
</template>

<script>
import _ from 'underscore';
import geo from 'geojs';
import { createNamespacedHelpers } from 'vuex';

import { restRequest, getApiRoot } from '@girder/core/rest';

import { MarkupState } from './AnnotationToolStore';

const { mapState } = createNamespacedHelpers('annotate');

export default {
  components: {
  },
  props: {
    image: {
      type: Object,
      default: null,
    },
  },
  data() {
    return {
    };
  },
  computed: {
    ...mapState([
      'markupState',
    ]),
  },
  watch: {
    image(newImage) {
      if (this.viewer) {
        this.viewer.exit();
        this.viewer = null;
        this.imageLayer = null;
        this.annotationLayer = null;
        this.pixelmap = null;
      }

      if (newImage) {
        restRequest({
          url: `image/${newImage._id}/tiles`,
          method: 'GET',
        }).done((resp) => {
          // TODO: Disable feature selection buttons until this is loaded
          this.initializeMap(resp);
        });
      }
    },
  },
  created() {
    this.viewer = null;
    this.imageLayer = null;
    this.annotationLayer = null;
    this.pixelmap = null;
  },
  mounted() {
  },
  beforeDestroy() {
    if (this.viewer) {
      this.viewer.exit();
    }
  },
  methods: {
    initializeMap(resp) {
      const params = geo.util.pixelCoordinateParams(
        this.$refs.pixelmap, resp.sizeX, resp.sizeY, resp.tileWidth, resp.tileHeight,
      );

      _.extend(params.map, {
        // TODO: allow rotation? (add actions to interactor and set allowRotation)
        allowRotation: false,
        interactor: geo.mapInteractor({
          actions: [{
            action: geo.geo_action.pan,
            input: 'left',
            modifiers: { shift: false, ctrl: false },
            owner: 'geo.mapInteractor',
            name: 'button pan',
          }, {
            action: geo.geo_action.zoom,
            input: 'right',
            modifiers: { shift: false, ctrl: false },
            owner: 'geo.mapInteractor',
            name: 'button zoom',
          }, {
            action: geo.geo_action.zoom,
            input: 'wheel',
            modifiers: { shift: false, ctrl: false },
            owner: 'geo.mapInteractor',
            name: 'wheel zoom',
          }],
        }),
      });
      params.map.max += 2;
      this.viewer = geo.map(params.map);

      _.extend(params.layer, {
        useCredentials: true,
        url: `${getApiRoot()}/image/${this.image._id}/tiles/{z}/{x}/{y}`,
      });
      this.imageLayer = this.viewer.createLayer('osm', params.layer);

      this.annotationLayer = this.viewer.createLayer('feature', {
        features: ['pixelmap'],
      });
      this.pixelmap = this.annotationLayer.createFeature('pixelmap', {
        selectionAPI: true,
        url: `${getApiRoot()}/image/${this.image._id}/superpixels`,
        position: {
          ul: { x: 0, y: 0 },
          lr: { x: resp.sizeX, y: resp.sizeY },
        },
        color: (dataValue) => {
          let color = {
            r: 0, g: 0, b: 0, a: 0,
          };
          const shownAlpha = 0.4;

          if (dataValue === MarkupState.ABSENT) {
            // This could be semi-transparent, to show "definite negative" tiles
            color.a = 0.0;
          } else if (dataValue === MarkupState.POSSIBLE) {
            color = geo.util.convertColor('#fafa00');
            color.a = shownAlpha;
          } else if (dataValue === MarkupState.DEFINITE) {
            color = geo.util.convertColor('#0000ff');
            color.a = shownAlpha;
          }
          // TODO: else, log error
          return color;
        },
      });
      this.annotationLayer.draw();

      this.clear();

      // TODO: This has to come after .clear, since that calls .geoOff, calling
      // .clear before this resolves will still break things
      this.pixelmap.geoOn(geo.event.pixelmap.prepared, () => {
        // loaded.resolve();
        // TODO: emit event?
      });
    },
    clear() {
      // Remove all active or displayed overlays
      this.pixelmap.data([]);
      this.pixelmap.visible(false);
      this.pixelmap.draw();

      this.pixelmap.geoOff();

      const interactor = this.viewer.interactor();
      // TODO: change this to add and remove actions
      interactor.hasAction(undefined, 'button pan').input = { left: true };
      interactor.hasAction(undefined, 'button zoom').input = { right: true };
    },
    activate(featureValues) {
      /* Enable drawing on the map, with an optional set of values to pre-fill. */
      this.clear();

      const interactor = this.viewer.interactor();
      // TODO: change this to add and remove actions
      interactor.hasAction(undefined, 'button zoom').input = { middle: true };
      interactor.hasAction(undefined, 'button pan').input = { right: true };

      const setSuperpixel = (index, value) => {
        const data = this.pixelmap.data();
        if (!data) {
          // TODO: this should never happen, remove once features can be cleard
          return;
        }
        if (data[index] !== value) {
          data[index] = value;
          this.pixelmap.data(data);
          this.pixelmap.draw();
        }
      };
      this.pixelmap.geoOn(geo.event.feature.mousemove, (evt) => {
        if (evt.mouse.buttons.left) {
          if (evt.mouse.modifiers.shift) {
            setSuperpixel(evt.index, MarkupState.ABSENT);
          } else {
            setSuperpixel(evt.index, this.markupState);
          }
        }
      });
      this.pixelmap.geoOn(geo.event.feature.mouseclick, (evt) => {
        if (evt.mouse.buttonsDown.left) {
          if (evt.mouse.modifiers.shift) {
            setSuperpixel(evt.index, MarkupState.ABSENT);
          } else {
            setSuperpixel(evt.index, this.markupState);
          }
        }
      });

      let fillFeatureValues = featureValues;
      if (!fillFeatureValues) {
        fillFeatureValues = new Array(this.pixelmap.maxIndex() + 1);
        fillFeatureValues.fill(MarkupState.ABSENT);
      }

      this.pixelmap.data(fillFeatureValues);
      this.pixelmap.visible(true);
      this.pixelmap.draw();
    },
    getActiveValues() {
      /* Return an array representing the current user-drawn values. */
      return this.pixelmap.data();
    },
    display(featureValues) {
      /* Display a view-only feature on the map. */
      this.clear();

      this.pixelmap.data(featureValues || []);
      this.pixelmap.visible(true);
      this.pixelmap.draw();
    },
  },
};
</script>

<style lang="stylus" scoped>
</style>
