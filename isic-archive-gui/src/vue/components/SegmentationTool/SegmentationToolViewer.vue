<template>
  <div />
</template>

<script>
import Map from 'ol/Map';
import View from 'ol/View';
import Draw from 'ol/interaction/Draw';
import { Tile as TileLayer, Vector as VectorLayer } from 'ol/layer';
import { OSM, Vector as VectorSource } from 'ol/source';

export default {
  name: 'SegmentationToolViewer',
  props: {
    drawing: {
      type: Boolean,
      default: false,
    },
  },
  data() {
    return {
      // TODO: Store as static / non-reactive
      map: null,
      vectorSource: null,
      polygonDraw: null,
    };
  },
  watch: {
    drawing() {
      if (this.drawing) {
        this.enablePolygonDraw();
      } else {
        this.disablePolygonDraw();
      }
    },
  },
  mounted() {
    this.vectorSource = new VectorSource({
      wrapX: false,
    });

    this.map = new Map({
      layers: [
        new TileLayer({
          source: new OSM(),
        }),
        new VectorLayer({
          source: this.vectorSource,
        }),
      ],
      target: this.$el,
      view: new View({
        center: [-11000000, 4600000],
        zoom: 4,
      }),
    });
  },
  methods: {
    enablePolygonDraw() {
      if (!this.polygonDraw) {
        this.polygonDraw = new Draw({
          source: this.vectorSource,
          type: 'Polygon',
        });
        this.map.addInteraction(this.polygonDraw);
      }
    },
    disablePolygonDraw() {
      if (this.polygonDraw) {
        this.map.removeInteraction(this.polygonDraw);
        this.polygonDraw = null;
      }
    },
  },
};
</script>
