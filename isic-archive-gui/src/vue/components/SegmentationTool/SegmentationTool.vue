<template>
  <div class="container-fluid">
    <div class="row">
      <div class="col-sm-3">
        <label for="drawing-enabled">
          Enable drawing
        </label>
        <input
          id="drawing-enabled"
          v-model="drawing"
          type="checkbox"
        >
      </div>
      <div class="col-sm-9">
        <segmentation-tool-viewer :drawing="drawing" />
      </div>
    </div>
  </div>
</template>

<script>
import SegmentationToolViewer from './SegmentationToolViewer.vue';

export default {
  name: 'SegmentationTool',
  components: {
    SegmentationToolViewer,
  },
  props: {
    imageId: {
      type: String,
      required: true,
    },
  },
  data() {
    return {
      drawing: false,
    };
  },
};
</script>
