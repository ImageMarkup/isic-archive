<template lang="pug">
table.table.table-condensed
  tr
    td.dataset-info-label Unique ID
    td
      code {{ dataset._id }}
  tr
    td.dataset-info-label Name
    td {{ dataset.name }}
  tr
    td.dataset-info-label Description
    td {{ dataset.description }}
  tr
    td.dataset-info-label License
    td {{ dataset.license }}
  tr
    td.dataset-info-label Attribution
    td {{ dataset.attribution }}
  tr
    td.dataset-info-label Created
    td {{ dataset.created | formatDate }}
</template>

<script>
import { formatDate as girderFormatDate, DATE_SECOND } from '@girder/core/misc';

export default {
  filters: {
    formatDate(value) {
      return girderFormatDate(value, DATE_SECOND);
    },
  },
  props: {
    dataset: {
      type: Object,
      required: true,
    },
  },
  data() {
    return {};
  },
};
</script>

<style lang="stylus" scoped>
table
  .dataset-info-label
    font-weight bold
    width 100px
</style>
