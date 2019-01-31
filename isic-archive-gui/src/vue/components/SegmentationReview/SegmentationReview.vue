<template lang="pug">
.container-fluid
  .row
    .col-md-3
      h2 Segmentation Review
      template(v-if='loading')
        spinner.pull-left(message='Loading...')
      template(v-else)
        table.table.table-condensed
          tr
            td.info-label Dataset Name
            td {{ dataset.name }}
          tr
            td.info-label Dataset Description
            td {{ dataset.description }}
          tr
            td.info-label Image ID
            td
              code {{ image._id }}
          tr
            td.info-label Image Name
            td {{ image.name }}
          tr
            td.info-label Segmentation
            td(v-if='segmentations.length').
              {{ activeSegmentationIndex + 1 }} of {{ segmentations.length }}
            td(v-else) (none)
        form(@submit.prevent='confirm')
          .review-button-container.btn-group-vertical.btn-group-lg(
            v-if='segmentations.length'
          )
            button.btn(
              type='button',
              :class='approveButtonClass',
              @click='approvalStatusClicked($event, ApprovalStatus.APPROVE)'
            ) Approve
            button.btn(
              type='button',
              :class='rejectButtonClass',
              @click='approvalStatusClicked($event, ApprovalStatus.REJECT)'
            ) Reject
          .submit-button-container
            button.btn.btn-primary.btn-lg(
              type='submit',
              :class='submitButtonClass',
              :disabled='!allowSubmit'
            )
              span(v-if='segmentations.length') Confirm
              span(v-else) Continue
        a(@click='showKeyboardShortcuts')
          i.icon-help-circled
          | Keyboard Shortcuts
        transition(name='spinner')
          spinner(
            v-if='loading || waiting',
            :message='spinnerMessage'
          )
    .col-md-9
      img.segmentation-thumbnail(
        v-if='activeSegmentationUrl',
        :src='activeSegmentationUrl'
      )
</template>

<script>
import { createNamespacedHelpers } from 'vuex';
import { getApiRoot } from '@girder/core/rest';
import Spinner from 'vue-simple-spinner';

import router from '../../../router';
import { showAlertDialog } from '../../../common/utilities';

import { WorkflowState } from './SegmentationReviewStore';

const {
  mapState, mapGetters, mapMutations, mapActions,
} = createNamespacedHelpers('segmentationReview');

const ApprovalStatus = {
  APPROVE: 'approve',
  REJECT: 'reject',
};

export default {
  components: {
    Spinner,
  },
  props: {
    datasetId: {
      type: String,
      required: true,
    },
  },
  data() {
    return {
      ApprovalStatus,
      approvalStatus: '',
      thumbnailWidth: 768,
    };
  },
  computed: Object.assign({
    loading() {
      return !(this.dataset && this.image);
    },
    waiting() {
      return this.workflowState === WorkflowState.SUBMITTING
                   || this.workflowState === WorkflowState.LOADING;
    },
    allowSubmit() {
      // Allow submitting when the image has no segmentations
      if (!this.waiting && !this.segmentations.length) {
        return true;
      }

      // Allow submitting if a status is selected
      return this.approvalStatus.length > 0;
    },
    spinnerMessage() {
      let message = '';
      switch (this.workflowState) {
        case WorkflowState.SUBMITTING:
          message = 'Submitting review...';
          break;
        case WorkflowState.LOADING:
          message = 'Loading image...';
          break;
        default:
          break;
      }
      return message;
    },
    approveButtonClass() {
      const active = this.approvalStatus === ApprovalStatus.APPROVE;
      return {
        'btn-default': !active,
        'btn-success': active,
        disabled: this.waiting,
      };
    },
    rejectButtonClass() {
      const active = this.approvalStatus === ApprovalStatus.REJECT;
      return {
        'btn-default': !active,
        'btn-danger': active,
        disabled: this.waiting,
      };
    },
    submitButtonClass() {
      return {
        disabled: this.waiting,
      };
    },
    activeSegmentationUrl() {
      if (!this.activeSegmentation) {
        return null;
      }
      return `${getApiRoot()}/segmentation/${this.activeSegmentation._id}`
                   + `/thumbnail?contentDisposition=inline&width=${this.thumbnailWidth}`;
    },
  }, mapState([
    'dataset',
    'image',
    'segmentations',
    'activeSegmentationIndex',
    'workflowState',
  ]), mapGetters([
    'activeSegmentation',
  ])),
  watch: {
    workflowState(newState) {
      if (newState === WorkflowState.IDLE) {
        this.approvalStatus = '';
      }

      if (newState === WorkflowState.FINISHED) {
        showAlertDialog({
          text: '<h4>All segmentations have been reviewed.</h4>',
          escapedHtml: true,
          callback: () => {
            router.navigate('tasks', { trigger: true });
          },
        });
      }
    },
  },
  created() {
  },
  mounted() {
    this.loadDataset({ id: this.datasetId });
    window.addEventListener('keydown', this.onKeyDown);
  },
  beforeDestroy() {
    window.removeEventListener('keydown', this.onKeyDown);
  },
  methods: Object.assign({
    showKeyboardShortcuts() {
      // TODO: Support Vue-based modal in Backbone app?
      showAlertDialog({
        text: '<h4>Keyboard Shortcuts</h4>'
                      + '<table>'
                      + '<tr><td style="text-align:right; padding-right: 10px; white-space: nowrap;">'
                      + '<kbd class="isic-kbd">x</kbd> or <kbd class="isic-kbd">]</kbd></td><td>Approve segmentation</td></tr>'
                      + '<tr><td style="text-align:right; padding-right: 10px; white-space: nowrap;">'
                      + '<kbd class="isic-kbd">z</kbd> or <kbd class="isic-kbd">[</kbd></td><td>Reject segmentation</td></tr>'
                      + '<tr><td style="text-align:right; padding-right: 10px; white-space: nowrap;">'
                      + '<kbd class="isic-kbd">Enter</kbd> or <kbd class="isic-kbd">Space</kbd></td><td>Confirm selection and advance to next segmentation</td></tr>',
        escapedHtml: true,
      });
    },
    approvalStatusClicked(event, status) {
      this.setApprovalStatus(status);

      // Remove focus from button so that 'confirm' keyboard shortcuts work as expected
      event.currentTarget.blur();
    },
    setApprovalStatus(status) {
      if (this.workflowState !== WorkflowState.IDLE) {
        return;
      }

      if (this.activeSegmentation) {
        this.approvalStatus = status;
      }
    },
    confirm() {
      if (this.workflowState !== WorkflowState.IDLE) {
        return;
      }

      // Continue to next image, e.g. when this image has no segmentations to review
      // TODO: Add endpoint that only sends images that have segmentations to review?
      if (!this.segmentations.length) {
        this.loadNextImage({ datasetId: this.dataset._id });
        return;
      }

      // Ignore event if user hasn't approved or rejected the segmentation
      if (!this.approvalStatus) {
        return;
      }

      // Submit segmentation review
      const approved = this.approvalStatus === ApprovalStatus.APPROVE;
      this.submitReview({
        segmentationId: this.activeSegmentation._id,
        approved,
      });
    },
    onKeyDown(event) {
      switch (event.key) {
        case 'z':
        case 'Z':
        case '[':
          this.setApprovalStatus(ApprovalStatus.REJECT);
          break;
        case 'x':
        case 'X':
        case ']':
          this.setApprovalStatus(ApprovalStatus.APPROVE);
          break;
        case 'Enter':
        case ' ':
          event.preventDefault();
          this.confirm();
          break;
        default:
          break;
      }
    },
  }, mapMutations([
  ]), mapActions([
    'loadDataset',
    'loadNextImage',
    'submitReview',
  ])),
};
</script>

<style lang="stylus" scoped>
table
  .info-label
    font-weight bold
    width 150px
    vertical-align top

form
  .btn
    width 100%
    outline none !important

.review-button-container
  width 100%

.submit-button-container
  margin 15px 0px

.segmentation-thumbnail
  border 1px solid #000

.spinner-enter-active
.spinner-leave-active
  transition opacity .3s

.spinner-enter
.spinner-leave-to
  opacity 0
</style>
