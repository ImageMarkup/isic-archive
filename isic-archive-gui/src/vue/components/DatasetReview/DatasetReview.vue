<template lang="pug">
.container-fluid
  .row
    .col-md-12
      h2 Dataset Review
  .row
    .col-md-6
      dataset-info(
        v-if='dataset',
        :dataset='dataset'
      )
    .submit-container.col-md-6
      .submit-info.
        Flagged images will be quarantined. Non-flagged images will be submitted for segmentation.
      .submit-button.btn.btn-success(@click='submitReview') Submit
  .row
    .col-md-12
      span Flagged images:&nbsp;
      span(
        v-for='(image, index) in flaggedImages',
        :key='image._id') {{ image.name }}
        //- Add comma after each name except the last. Use code to represent space to avoid ending a
            line with a space.
        template(v-if='index < flaggedImages.length - 1') ,&#x20;
  .row
    .image-container.col-lg-12.col-md-12
      dataset-review-image(
        v-for='(image, index) in images',
        :image='image',
        :key='image._id',
        @toggleFlagged='toggleFlagged(index)')
</template>

<script>
import { createNamespacedHelpers } from 'vuex';

import { getApiRoot } from '@girder/core/rest';

import DatasetInfo from './DatasetInfo.vue';
import DatasetReviewImage from './DatasetReviewImage.vue';
import { SubmissionState } from './DatasetReviewStore';

const {
  mapState, mapGetters, mapMutations, mapActions,
} = createNamespacedHelpers('datasetReview');

export default {
  components: {
    DatasetInfo,
    DatasetReviewImage,
  },
  props: {
    datasetId: {
      type: String,
      required: true,
    },
  },
  data() {
    return {};
  },
  computed: Object.assign({
  }, mapState([
    'dataset',
    'images',
    'submissionState',
  ]), mapGetters([
    'flaggedImages',
  ])),
  watch: {
    submissionState(newState) {
      if (newState === SubmissionState.SUBMITTED) {
        const redirectUrl = `${getApiRoot()}/task/me/review/redirect?datasetId=${this.dataset._id}`;
        window.location.replace(redirectUrl);
      }
    },
  },
  created() {
  },
  mounted() {
    this.loadDataset({ id: this.datasetId });
  },
  methods: Object.assign({
  }, mapMutations([
    'toggleFlagged',
  ]), mapActions([
    'loadDataset',
    'submitReview',
  ])),
};
</script>

<style lang="stylus" scoped>
.submit-container
  display flex // enable flex context for children
  justify-content flex-end // align children to right
  align-items flex-start // align children to top

  .submit-info
    padding-right 10px

.image-container
  display flex // enable flex context for children
  flex-wrap wrap // wrap children onto multiple lines
</style>
