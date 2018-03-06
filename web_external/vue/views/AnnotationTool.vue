<template lang="pug">
.annotation-tool-container.container-fluid
  .isic-page.row
    .isic-pane.col-sm-3
      .header
        .info-group
          span.title ISIC Annotation Tool
          a.pull-right(href='/') Return home.
        .info-group
          div(v-if='image')
            span #[b Image:]&nbsp;{{ image.name }}
        .info-group
          div(v-if='user')
            span #[b User:]&nbsp;{{ user.name() }}
        .info-group
          .dropdown
            button.btn.btn-warning.dropdown-toggle(
              type='button',
              data-toggle='dropdown'
            )
              span Flag Image&nbsp;
              span.caret
            ul.dropdown-menu
              li
                a(@click='setFlagStatus("ok")') Unflagged
              li
                a(@click='setFlagStatus("phi")') Contains PHI
              li
                a(@click='setFlagStatus("quality")') Low optical quality
              li
                a(@click='setFlagStatus("zoom")') Inadequate zoom factor
              li
                a(@click='setFlagStatus("inappropriate")') Clinically inappropriate
              li.divider
              li
                a(@click='flag("other")') Other reason
            span.flag-status
              span #[b Flag Status:]&nbsp;{{ flagStatus }}
      .annotation(v-if='questions.length > 0')
        h3.annotation-header Global Features
        annotation-tool-global-features
      .annotation(v-if='questions.length > 0')
        h3.annotation-header Local Features
        .annotation-section
          annotation-tool-local-features(
            :activeFeatureId='activeFeatureId',
            @featureActivated='onFeatureActivated',
            @featureDeactivated='onFeatureDeactivated',
            @displayFeature='onDisplayFeature',
            @deleteFeature='onDeleteFeature'
          )
      .annotation-section
        .btn-group
          template(v-if='showReview')
            button.btn.btn-info(
              type='button',
              @click='setShowReview(false)'
            ) Continue editing
          template(v-else)
            button.btn.btn-info(
              type='button',
              @click='reset'
            ) Reset current
        .btn-group.pull-right
          template(v-if='showReview')
            button.btn.btn-success(
              type='button',
              @click='submitAnnotation'
            ) Submit
          template(v-else)
            button.btn.btn-success(
              type='button',
              @click='setShowReview(true)'
            ) Review
    .isic-map.col-sm-9
      annotation-tool-viewer.isic-map(
        ref='viewer',
        :image='image'
      )
</template>

<script>
import { createNamespacedHelpers } from 'vuex';

import { getApiRoot } from 'girder/rest';
import { getCurrentUser } from 'girder/auth';

import AnnotationToolGlobalFeatures from './AnnotationToolGlobalFeatures.vue';
import AnnotationToolLocalFeatures from './AnnotationToolLocalFeatures.vue';
import AnnotationToolViewer from './AnnotationToolViewer.vue';

import { MarkupState, SubmissionState } from '../store/modules/annotate';

const { mapState, mapGetters, mapMutations, mapActions } = createNamespacedHelpers('annotate');

// TODO: fix compilation using object spread operator
// TODO: fix compilation using async/await
// TODO: make viewer more reactive? (i.e. remove this.$refs.viewer calls where possible)
export default {
    components: {
        AnnotationToolGlobalFeatures: AnnotationToolGlobalFeatures,
        AnnotationToolLocalFeatures: AnnotationToolLocalFeatures,
        AnnotationToolViewer: AnnotationToolViewer
    },
    props: {
        annotationId: {
            type: String,
            required: true
        }
    },
    data() {
        return {
            user: null
        };
    },
    computed: Object.assign({
    }, mapState([
        'study',
        'image',
        'flagStatus',
        'showReview',
        'responses',
        'markups',
        'activeFeatureId',
        'submissionState'
    ]), mapGetters([
        'questions'
    ])),
    watch: {
        questions() {
            this.resetResponses();
            this.resetMarkups();
        },
        showReview(newValue) {
            if (newValue && this.activeFeatureId) {
                this.deactivateFeature(this.activeFeatureId);
            }
        },
        submissionState(newState) {
            if (newState === SubmissionState.SUBMITTED) {
                const redirectUrl = `${getApiRoot()}/task/me/annotation/redirect?studyId=${this.study._id}`;
                window.location.replace(redirectUrl);
            }
        }
    },
    created() {
    },
    mounted() {
        this.user = getCurrentUser();
        this.getAnnotation({id: this.annotationId});
    },
    methods: Object.assign({
        reset() {
            if (this.activeFeatureId) {
                this.deactivateFeature(this.activeFeatureId);
            }
            this.setActiveFeatureId(null);
            this.setShowReview(false);
            this.setMarkupState(MarkupState.DEFINITE);
            this.resetResponses();
            this.resetMarkups();
        },
        resetMarkups() {
            this.setMarkups({});
        },
        resetResponses() {
            const responses = {};
            this.questions.forEach((question) => {
                responses[question.id] = null;
            });
            this.setResponses(responses);
        },
        deactivateFeature(featureId) {
            // Save feature markup
            // Optimization: freeze array so that it isn't reactive
            const values = this.$refs.viewer.getActiveValues();
            this.setMarkup({
                featureId: featureId,
                values: Object.freeze(values)
            });
            this.$refs.viewer.clear();

            this.setActiveFeatureId(null);
        },
        onFeatureActivated(featureId) {
            if (this.activeFeatureId) {
                this.deactivateFeature(this.activeFeatureId);
            }
            this.setActiveFeatureId(featureId);

            let markup = null;
            if (this.markups.hasOwnProperty(featureId)) {
                // Copy frozen array to allow editing
                markup = this.markups[featureId].slice(0);
            }
            this.$refs.viewer.activate(markup);
        },
        onFeatureDeactivated(featureId) {
            this.deactivateFeature(featureId);
        },
        onDisplayFeature(featureId) {
            if (featureId) {
                const markup = this.markups[featureId];
                this.$refs.viewer.display(markup);
            } else {
                this.$refs.viewer.clear();
            }
        },
        onDeleteFeature(featureId) {
            if (this.activeFeatureId === featureId) {
                this.deactivateFeature(featureId);
            }

            this.setMarkup({
                featureId: featureId,
                values: null
            });
        }
    }, mapMutations([
        'setFlagStatus',
        'setShowReview',
        'setMarkupState',
        'setResponses',
        'setMarkups',
        'setMarkup',
        'setActiveFeatureId'
    ]), mapActions([
        'getAnnotation',
        'submitAnnotation'
    ]))
};
</script>

<style lang="stylus" scoped>
.annotation-tool-container
  background #000

.header
  background #171616
  color #fff
  font-weight 300
  padding 6px
  padding-top 10px
  padding-left 10px
  border-bottom 1px solid #333

.title
  font-size 15pt

.isic-page
  height calc(100vh - 9em)

.isic-map
  height 100%
  padding 0px

.isic-pane
  height 100%
  overflow-y auto
  padding 0px
  color #fff
  background #000

.info-group
  padding 6px

.flag-status
  padding-left 6px

.annotation
  .annotation-header
    background: #282727
    color: #fff
    padding 10px 6px 6px 10px
    border-bottom 1px solid #333

.annotation-section
  margin 0px
  padding 5px
</style>
