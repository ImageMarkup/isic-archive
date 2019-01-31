<template lang="pug">
.annotation-tool-features
  .alert.alert-warning.annotation-body-help
    i.icon-help-circled
    template(v-if='showReview')
      span Mouse over a feature type to display markup.
    template(v-else)
      span(v-if='anyActive') Markup regions with this feature type.
      span(v-else) Click a feature type to select it for markup.
  .alert.alert-info.annotation-body-help
    i.icon-info-circled
    span(v-if='anyActive')
      | #[b Left-click] to markup tiles.<br>
      | #[b Shift-left-click] to erase tiles.<br>
      | #[b Mouse wheel] to zoom in and out.<br>
      | #[b Right-click and drag] to move while zoomed in.
    span(v-else)
      | #[b Mouse wheel] to zoom in and out.<br>
      | #[b Left-click and drag] to move while zoomed in.<br>
      | #[b Right-click and drag] to zoom in and out.<br>
      | &nbsp;
  div.annotation-section(v-show='!showReview')
    label Confidence&nbsp;
    .btn-group(data-toggle='buttons')
      label.annotation-radio-btn.btn.btn-default(
        :class='{active: markupState === 1.0}'
      )
        input(
          type='radio',
          name='certainty',
          v-model.number='certainty'
          :value='1.0'
        )
        span 100%
      label.annotation-radio-btn.btn.btn-default(
        :class='{active: markupState === 0.5}'
      )
        input(
          type='radio',
          name='certainty',
          v-model.number='certainty'
          :value='0.5'
        )
        span 50%?
  div.annotation-section
    template(v-if='showReview')
      span(
        v-for='feature in markedupFeatures',
        :key='feature.id',
      )
        button.annotation-radio-btn.annotation-features-activate.btn.btn-default(
          type='button',
          @mouseenter='onMouseEnter(feature.id)',
          @mouseleave='onMouseLeave(feature.id)'
        )
          span {{ feature.id }}

    template(v-else)
      span(
        v-for='feature in features',
        :key='feature.id'
      )
        button.annotation-radio-btn.annotation-features-activate.btn.btn-default(
          type='button',
          :class='{active: isActive(feature.id)}',
          @click='onClick(feature.id)'
        )
          span {{ feature.id }}
        button.annotation-radio-btn.annotation-features-delete.btn.btn-default(
          v-if='markedupFeatureIds.includes(feature.id)',
          type='button',
          @click='onDelete(feature.id)'
        )
          i.icon-cancel
</template>

<script>
import { createNamespacedHelpers } from 'vuex';

const { mapState, mapGetters, mapMutations } = createNamespacedHelpers('annotate');

export default {
  props: {
    activeFeatureId: {
      type: String,
      default: null,
    },
  },
  data() {
    return {};
  },
  computed: Object.assign({
    anyActive() {
      return this.activeFeatureId !== null;
    },
    markedupFeatures() {
      return this.features.filter(feature => this.markedupFeatureIds.includes(feature.id));
    },
    certainty: {
      get() {
        return this.markupState;
      },
      set(value) {
        this.setMarkupState(value);
      },
    },
  }, mapState([
    'showReview',
    'markupState',
  ]), mapGetters([
    'features',
    'markedupFeatureIds',
  ])),
  methods: Object.assign({
    isActive(featureId) {
      return this.activeFeatureId === featureId;
    },
    onClick(featureId) {
      if (this.isActive(featureId)) {
        this.$emit('featureDeactivated', featureId);
      } else {
        this.$emit('featureActivated', featureId);
      }
    },
    onMouseEnter(featureId) {
      this.$emit('displayFeature', featureId);
    },
    onMouseLeave() {
      this.$emit('displayFeature', null);
    },
    onDelete(featureId) {
      this.$emit('deleteFeature', featureId);
    },
  }, mapMutations([
    'setMarkupState',
  ])),
};
</script>

<style lang="stylus" scoped>
.annotation-section
  margin 0px
  padding 5px

.annotation-body-help
  display flex
  margin-bottom 0px
  border-radius 0px

.annotation-radio-btn
  color #ffffff
  background-color #333333
  border-radius 0px
  &:focus
    color #ffffff
    background-color #333333
  &:hover
    color #ffffff
    background-color #f2b866
  &.active
    background-color #f0ad4e

.annotation-features-activate
  width 80%
  text-align left
  white-space normal
  margin-right 3px

.annotation-features-delete
  color #ffffff
  background-color #99190d
  &:hover
    background-color #f05c4e
</style>
