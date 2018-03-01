<template lang="pug">
.container-fluid
  .row
    .col-md-12
      h2 Dataset Review
  .row
    .header.col-md-12
      template(v-if='dataset')
        .dataset-info Name:&nbsp;#[b {{ dataset.name }}]
        .dataset-info Created:&nbsp;#[b {{ dataset.created }}]
        .dataset-info Updated:&nbsp;#[b {{ dataset.updated }}]
      .submit-info Flagged images will be quarantined. Non-flagged images will be submitted for segmentation.
      .submit-button.btn.btn-success(@click='submitReview') Submit
  .row
    .col-md-12
      span Flagged images:&nbsp;
      span(
        v-for='(image, index) in flaggedImages',
        :key='image._id') {{ image.name }}
        //- Add comma after each name except the last. Use code to represent space to avoid ending a line with a space.
        template(v-if='index < flaggedImages.length - 1') ,&#x20;
  .row
    .col-lg-12.col-md-12
      dataset-review-image(
        v-for='(image, index) in images',
        :image='image',
        :key='image._id',
        @toggleFlagged='toggleFlagged(index)')
</template>

<script>
import { createNamespacedHelpers } from 'vuex';

import { getApiRoot } from 'girder/rest';

import DatasetReviewImage from './DatasetReviewImage.vue';
import { SubmissionState } from './DatasetReviewStore';

const { mapState, mapGetters, mapMutations, mapActions } = createNamespacedHelpers('datasetReview');

export default {
    components: {
        DatasetReviewImage: DatasetReviewImage
    },
    props: {
        datasetId: {
            type: String,
            required: true
        }
    },
    data() {
        return {};
    },
    computed: Object.assign({
    }, mapState([
        'dataset',
        'images',
        'submissionState'
    ]), mapGetters([
        'flaggedImages'
    ])),
    watch: {
        submissionState(newState) {
            if (newState === SubmissionState.SUBMITTED) {
                const redirectUrl = `${getApiRoot()}/task/me/review/redirect?datasetId=${this.dataset._id}`;
                window.location.replace(redirectUrl);
            }
        }
    },
    created() {
    },
    mounted() {
        this.getDataset({id: this.datasetId});
        this.getReviewImages({id: this.datasetId});
    },
    methods: Object.assign({
    }, mapMutations([
        'toggleFlagged'
    ]), mapActions([
        'getDataset',
        'getReviewImages',
        'submitReview'
    ]))
};
</script>

<style lang="stylus" scoped>
.header
  display flex
  align-items center

  .dataset-info
    padding-right 10px

  .submit-info
    padding-right 10px
    margin-left auto
</style>
