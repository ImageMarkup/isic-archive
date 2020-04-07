<template>
  <div class="isic-form-page isic-upload-batch-container">
    <h2 class="isic-page-title">
      Upload batch
    </h2>

    <div class="isic-form-container">
      <div class="isic-form-group">
        <h3>
          Select dataset
        </h3>
        <div class="form-group">
          <SelectDataset
            v-model="dataset"
            :access-level="AccessType.WRITE"
          />
        </div>
      </div>

      <div class="isic-form-group">
        <DatasetInfoWidget :dataset="dataset" />
      </div>

      <div class="isic-form-group">
        <h3>
          Upload images
        </h3>
        <div class="isic-upload-description-container">
          Upload a ZIP file of images.
        </div>
        <div class="isic-upload-container">
          <FileSelect
            v-model="zipFile"
            accept=".zip"
          />
        </div>
      </div>

      <div class="isic-form-group">
        <h3>
          Licensing
        </h3>
        <p>
          Enter your name to electronically sign the contributor license agreement.
        </p>
        <div class="form-group">
          <label class="control-label">
            Contributor license agreement
          </label>
          <div id="isic-terms-of-use-container" />
        </div>
        <div class="form-group">
          <label
            class="control-label"
            for="isic-upload-batch-agreement-signature"
          >
            Electronic signature
          </label>
          <input
            id="isic-upload-batch-agreement-signature"
            v-model.trim="signature"
            class="form-control input-sm"
            type="text"
            placeholder="Enter your name"
          >
        </div>
      </div>

      <form
        id="isic-upload-batch-form"
        @submit.prevent="submit"
      >
        <button
          id="isic-upload-batch-submit"
          class="btn btn-primary btn-md"
          type="submit"
          :disabled="!submitReady"
        >
          Submit
        </button>
      </form>
    </div>
  </div>
</template>

<script>
import S3 from 'aws-sdk/clients/s3';
import _ from 'underscore';

import { AccessType } from '@girder/core/constants';
import { restRequest } from '@girder/core/rest';

import router from '../router';
import { showAlertDialog } from '../common/utilities';

import DatasetInfoWidget from './DatasetInfoWidget.vue';
import FileSelect from './FileSelect.vue';
import SelectDataset from './SelectDataset.vue';

export default {
  name: 'UploadBatch',
  components: {
    DatasetInfoWidget,
    FileSelect,
    SelectDataset,
  },
  data() {
    return {
      dataset: null,
      zipFile: null,
      signature: '',
      uploading: false,
      AccessType,
    };
  },
  computed: {
    submitReady() {
      return this.dataset && this.zipFile && this.signature && !this.uploading;
    },
  },
  methods: {
    reset() {

    },
    async submit() {
      this.uploading = true;

      const initUpload = await restRequest({
        method: 'POST',
        url: `dataset/${this.dataset.id}/zip`,
        data: {
          signature: this.signature,
          filename: this.zipFile.name,
        },
      });

      const s3Options = {
        apiVersion: '2006-03-01',
        accessKeyId: initUpload.accessKeyId,
        secretAccessKey: initUpload.secretAccessKey,
        sessionToken: initUpload.sessionToken,
      };
      if (process.env.NODE_ENV !== 'production') {
        Object.assign(s3Options, {
          endpoint: 'http://isic-archive.test:9000',
          s3ForcePathStyle: true,
          sessionToken: null,
        });
      }
      const s3 = new S3(s3Options);

      try {
        await s3.upload({
          Bucket: initUpload.bucketName,
          Key: initUpload.objectKey,
          Body: this.zipFile,
          // TODO: this.zipFile name?
        })
          .on('httpUploadProgress', (evt) => { // eslint-disable-line no-unused-vars
            // TODO: Render a progress bar
            // console.log('Progress:', evt.loaded, '/', evt.total); // eslint
          })
          .promise();
      } catch (e) {
        await restRequest({
          method: 'DELETE',
          url: `dataset/${this.dataset.id}/zip/${initUpload.batchId}`,
        });

        showAlertDialog({
          text: `<h4>Error uploading batch</h4><br>${_.escape(e.toString())}`,
          escapedHtml: true,
        });

        this.uploading = false;
        return;
      }

      await restRequest({
        method: 'POST',
        url: `dataset/${this.dataset.id}/zip/${initUpload.batchId}`,
      });

      showAlertDialog({
        text: '<h4>Batch successfully uploaded.</h4>',
        escapedHtml: true,
        callback: () => {
          router.navigate(`dataset/${this.dataset.id}/metadata/register`, { trigger: true });
        },
      });
    },
  },
};
</script>

<style lang="stylus" scoped>
</style>
