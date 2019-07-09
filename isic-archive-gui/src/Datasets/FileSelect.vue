<template>
  <div>
    <vueDropzone
      id="vue-dropzone"
      ref="imageDropzone"
      :options="dropzoneOptions"
      :use-custom-slot="true"
      @vdropzone-file-added="onFileAdded"
      @vdropzone-removed-file="onFileRemoved"
      @vdropzone-max-files-exceeded="onMaxFilesExceeded"
    >
      <i class="icon-upload-cloud" />
      <p>Drag and Drop File or Click Here</p>
    </vueDropzone>
    <button
      class="remove-file-button btn btn-default btn-md"
      :disabled="!active || !selectedFile"
      @click="resetFile"
    >
      Clear Selected File
    </button>
  </div>
</template>

<script>
import vueDropzone from 'vue2-dropzone';
import 'vue2-dropzone/dist/vue2Dropzone.min.css';

export default {
  name: 'FileSelect',
  components: {
    vueDropzone,
  },
  props: {
    accept: {
      type: String,
      default: '',
    },
    active: {
      type: Boolean,
      default: true,
    },
    thumbnail: {
      type: Boolean,
      default: false,
    },
  },
  data() {
    return {
      selectedFile: null,
    };
  },
  computed: {
    dropzoneOptions() {
      return {
        createImageThumbnails: this.thumbnail,
        maxFiles: 1,
        acceptedFiles: this.accept,

        thumbnailWidth: 250,
        thumbnailHeight: null,

        // Required option
        url: '#',
        // Don't automatically do anything with added files
        autoProcessQueue: false,
      };
    },
  },
  methods: {
    onFileAdded(file) {
      this.selectedFile = file;
      this.$refs.imageDropzone.dropzone.emit('complete', file);

      this.$emit('input', this.selectedFile);
    },
    onFileRemoved() {
      if (this.$refs.imageDropzone.getAcceptedFiles().length === 0) {
        this.selectedFile = null;
        this.$emit('input', this.selectedFile);
      }
    },
    onMaxFilesExceeded(file) {
      this.$refs.imageDropzone.removeFile(file);
    },
    resetFile() {
      this.$refs.imageDropzone.removeAllFiles();
    },
  },
};
</script>

<style lang="stylus" scoped>
#vue-dropzone
  border 2px dashed #dddddd
  border-radius 8px
  padding 0

  .dz-message
    .icon-upload-cloud
      font-size 100px

  // Use >>> combinator so that scoped style in this component affects the child dropzone component
  >>> .dz-preview
    .dz-image
      img
        width 100%
        min-width 200px

.remove-file-button
  margin-top 10px
</style>
