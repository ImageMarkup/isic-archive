<template lang="pug">
.panel-group
  .panel.panel-default(
    v-for='question in questions',
    :key='question.id'
  )
    .panel-heading
      .panel-title
        a(
          data-toggle='collapse',
          :href='`#collapse_${question.id}`'
        ) {{ question.id }}
    .panel-collapse.in(:id='`collapse_${question.id}`')
      .panel-body
        template(v-if='showReview')
          label.question-option.review {{ selectedResponseName(question) }}
        template(v-else)
          div(
            v-for='choice in question.choices',
            :key='question.id + choice'
          )
            label.question-option
              input(
                type='radio',
                :name='question.id',
                :value='choice',
                :checked='choice === responses[question.id]',
                @change='onChange'
              )
              span {{ choice }}
</template>

<script>
import _ from 'underscore';
import { createNamespacedHelpers } from 'vuex';

const { mapState, mapGetters, mapMutations } = createNamespacedHelpers('annotate');

export default {
  data() {
    return {};
  },
  computed: Object.assign({
  }, mapState([
    'showReview',
    'responses',
  ]), mapGetters([
    'questions',
  ])),
  methods: Object.assign({
    selectedResponseName(question) {
      if (!_.has(this.responses, question.id)) {
        return null;
      }
      return this.responses[question.id];
    },
    onChange(event) {
      if (event.target.checked) {
        this.setResponse({
          questionId: event.target.name,
          response: event.target.value,
        });
      }
    },
  }, mapMutations([
    'setResponse',
  ])),
};
</script>

<style lang="stylus" scoped>
.panel-group
  padding-left 6px
  padding-right 6px

.panel
  border-radius 0px

.panel-heading
  background-color #f5f5f5
  color #333

  .panel-title
    font-size 16px

.panel-body
  background-color #333

.question-option
  font-weight 300

  &.review
  input[type=radio]:checked + span
    font-weight 700
    color #ffcc00
</style>
