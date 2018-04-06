<template lang="pug">
.isic-gallery-image(@click='toggleFlagged')
  img.img-responsive(
    :src='image.thumbnail',
    :style='imageStyle'
  )
  .overlay
    .flagged(v-show='image.flagged')
      .shade
      i.icon-flag
    .text.name {{ image.name }}
    .text.metadata(v-show='image.diagnosisStrings.length')
      span(v-for='diagnosisString in image.diagnosisStrings')
        span {{ diagnosisString }}
        br
</template>

<script>
import { createNamespacedHelpers } from 'vuex';

const { mapState } = createNamespacedHelpers('datasetReview');

export default {
    props: {
        image: {
            type: Object,
            required: true
        }
    },
    data() {
        return {};
    },
    computed: Object.assign({
        imageStyle() {
            return {
                width: `${this.thumbnailWidth}px`
            };
        }
    }, mapState([
        'thumbnailWidth'
    ])),
    methods: {
        toggleFlagged() {
            this.$emit('toggleFlagged');
        }
    }
};
</script>

<style lang="stylus" scoped>
.isic-gallery-image
  flex none
  position relative // ensure children can have absolute position
  margin 20px 20px
  cursor pointer
  height 0% // allow height to expand only to that of child image

  img
    border 1px solid black

  .overlay
    position absolute
    width 100%
    height 100%
    top 0
    left 0
    overflow hidden
    color white
    pointer-events none

    .flagged
      width 100%
      height 100%
      display flex // enable flex context for children
      justify-content center // center children horizontally
      align-items center // center children vertically

      .shade
        position absolute
        z-index 1
        width 100%
        height 100%
        background-color rgba(0, 0, 0, 0.6)
      i
        position absolute
        z-index 2
        font-size 50px

    .text
      z-index 3
      padding 5px
      background-color rgba(0, 0, 0, 0.6)

      &.name
        position absolute
        top 0
        left 0

      &.metadata
        position absolute
        bottom 0
        left 0
        word-wrap break-word

// FIXME: How to write general sibling combinator in stylus?
.isic-gallery-image > img:hover ~ .overlay > .text {
    opacity: 0.2;
}
</style>
