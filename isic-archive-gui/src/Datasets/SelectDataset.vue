<template lang="pug">
div
  select.form-control.input(v-model='dataset', @change.prevent='onChange')
    option(selected, disabled, value='null') Select a dataset...
    option(v-for='dataset in datasets', :value='dataset') {{ dataset.name() }}
  .create-dataset(v-if='canCreateDataset')
    a(href='#dataset/create') Create a new dataset
</template>

<script>
import DatasetModel from '../models/DatasetModel';

export default {
  props: {
    // Array of DatasetModel
    datasets: {
      type: Array,
      required: true,
    },
  },
  data() {
    return {
      dataset: null,
    };
  },
  computed: {
    canCreateDataset() {
      return DatasetModel.canCreate();
    },
  },
  methods: {
    onChange() {
      this.$emit('input', this.dataset);
    },
  },
};
</script>

<style lang="stylus" scoped>
.create-dataset
  margin-top 5px
</style>
