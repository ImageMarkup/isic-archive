<template>
  <div>
    <!-- TODO: This can be a v-autocomplete, to replace Select2 functionality -->
    <select
      class="form-control input"
      @input="selected"
    >
      <option
        selected
        disabled
        :value="null"
      >
        Select a dataset...
        {{ accessableDatasets.length ? ` (${accessableDatasets.length} available)` : '' }}
      </option>
      <option
        v-for="dataset in accessableDatasets"
        :key="dataset.id"
        :value="dataset.id"
      >
        {{ dataset.name() }}
      </option>
    </select>
    <div
      v-if="canCreateDataset"
      class="create-dataset"
    >
      Or
      <a href="#dataset/create">
        Create a new dataset
      </a>
    </div>
  </div>
</template>

<script>
import { AccessType } from '@girder/core/constants';

import DatasetCollection from '../collections/DatasetCollection';
import DatasetModel from '../models/DatasetModel';

export default {
  name: 'SelectDataset',
  model: {
    prop: 'dataset',
  },
  props: {
    accessLevel: {
      type: Number,
      default: AccessType.READ,
    },
  },
  data() {
    return {
      datasets: new DatasetCollection(),
    };
  },
  computed: {
    canCreateDataset() {
      return DatasetModel.canCreate();
    },
    accessableDatasets() {
      return this.datasets.filter((dataset) => dataset.get('_accessLevel') >= this.accessLevel);
    },
  },
  async created() {
    this.datasets.pageLimit = Number.MAX_SAFE_INTEGER;
    await this.datasets.fetch({ limit: 0 });
  },
  methods: {
    selected(event) {
      const selectedDatasetId = event.target.value;
      const selectedDataset = this.datasets.get(selectedDatasetId);
      this.$emit('input', selectedDataset);
    },
  },
};
</script>

<style lang="stylus" scoped>
.create-dataset
  margin-top 5px
</style>
