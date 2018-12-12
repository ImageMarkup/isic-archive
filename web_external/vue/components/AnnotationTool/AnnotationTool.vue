<template lang="pug">
.annotation-tool-container.container-fluid
  .isic-page.row
    .isic-pane.col-sm-3
      .header
        .info-group.title ISIC Annotation Tool
        .info-group #[b Image:]&nbsp;
          transition(name='image-name')
            span(v-if='image') {{ image.name }}
        .info-group.dropdown
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
              a(@click='setFlagStatus("other")') Other reason
          span.flag-status
            span #[b Flag Status:]&nbsp;{{ flagStatus }}
      .annotation(v-if='features.length > 0')
        h3.annotation-header Features
        .annotation-section
          annotation-tool-features(
            :activeFeatureId='activeFeatureId',
            @featureActivated='onFeatureActivated',
            @featureDeactivated='onFeatureDeactivated',
            @displayFeature='onDisplayFeature',
            @deleteFeature='onDeleteFeature'
          )
      .annotation(v-if='questions.length > 0')
        h3.annotation-header Questions
        annotation-tool-questions
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

import { showAlertDialog } from '../../../common/utilities';
import router from '../../../router';

import AnnotationToolQuestions from './AnnotationToolQuestions.vue';
import AnnotationToolFeatures from './AnnotationToolFeatures.vue';
import AnnotationToolViewer from './AnnotationToolViewer.vue';

import { MarkupState, SubmissionState } from './AnnotationToolStore';

const { mapState, mapGetters, mapMutations, mapActions } = createNamespacedHelpers('annotate');

// TODO: fix compilation using object spread operator
// TODO: fix compilation using async/await
// TODO: make viewer more reactive? (i.e. remove this.$refs.viewer calls where possible)
export default {
    components: {
        AnnotationToolQuestions: AnnotationToolQuestions,
        AnnotationToolFeatures: AnnotationToolFeatures,
        AnnotationToolViewer: AnnotationToolViewer
    },
    props: {
        studyId: {
            type: String,
            required: true
        }
    },
    data() {
        return {};
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
        'questions',
        'features'
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
                this.$refs.viewer.clear();

                // Reset state, preserving study
                const study = this.study;
                this.resetState();
                this.setStudy(study);

                this.getNextAnnotation({studyId: this.studyId});
            } else if (newState === SubmissionState.FINISHED) {
                showAlertDialog({
                    text: '<h4>All images in this study have been annotated.</h4>',
                    escapedHtml: true,
                    callback: () => {
                        router.navigate('tasks', {trigger: true});
                    }
                });
            }
        }
    },
    created() {
    },
    mounted() {
        this.getStudy({id: this.studyId});
        this.getNextAnnotation({studyId: this.studyId});
    },
    methods: Object.assign({
        reset() {
            if (this.activeFeatureId) {
                this.deactivateFeature(this.activeFeatureId);
            }
            this.setActiveFeatureId(null);
            if (this.showReview) {
                this.setShowReview(false);
            }
            this.setMarkupState(MarkupState.DEFINITE);
            this.resetResponses();
            this.resetMarkups();
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
        'resetState',
        'setStudy',
        'setFlagStatus',
        'setShowReview',
        'setMarkupState',
        'setMarkup',
        'setActiveFeatureId'
    ]), mapActions([
        'getNextAnnotation',
        'getStudy',
        'resetResponses',
        'resetMarkups',
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

.image-name-enter-active
.image-name-leave-active
  transition opacity .25s

.image-name-enter
.image-name-leave-to
  opacity 0
</style>
