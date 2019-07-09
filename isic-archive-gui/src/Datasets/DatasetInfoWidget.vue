<template>
  <div>
    <h3>
      Dataset
    </h3>
    <table class="table table-condensed isic-dataset-info-table">
      <tbody>
        <template v-if="dataset">
          <tr>
            <td class="isic-dataset-info-table-label">
              Name
            </td>
            <td>
              {{ dataset.name() }}
            </td>
          </tr>
          <tr>
            <td class="isic-dataset-info-table-label">
              Description
            </td>
            <td>
              {{ dataset.get('description') }}
            </td>
          </tr>
          <tr>
            <td class="isic-dataset-info-table-label">
              License
            </td>
            <td>
              {{ dataset.get('license') }}
            </td>
          </tr>
          <tr>
            <td class="isic-dataset-info-table-label">
              Attribution
            </td>
            <td>
              {{ dataset.get('attribution') }}
            </td>
          </tr>
          <tr v-if="dataset.canWrite()">
            <td class="isic-dataset-info-table-label">
              Owner
            </td>
            <td>
              {{ dataset.get('owner') }}
            </td>
          </tr>
        </template>
        <template v-else>
          <tr>
            <td class="isic-dataset-info-none-selected">
              None selected
            </td>
          </tr>
        </template>
      </tbody>
    </table>
  </div>
</template>

<script>
export default {
  name: 'UploadBatch',
  props: {
    dataset: {
      type: Object,
      default: null,
    },
  },
};
</script>

<style lang="stylus" scoped>
table.isic-dataset-info-table
  td
    border none !important

  .isic-dataset-info-table-label
    font-weight bold
    width 100px

  .isic-dataset-info-none-selected
    font-style italic
</style>
