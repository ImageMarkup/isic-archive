<template lang="pug">
.isic-upload-image-container
  .container
    .row
      .col-lg-12
        h2 Upload image to dataset
    .row
      .col-lg-3
        vue-dropzone#image-dropzone(
          ref='imageDropzone',
          @vdropzone-file-added='onFileAdded',
          @vdropzone-removed-file='onFileRemoved',
          @vdropzone-thumbnail='onThumbnailGenerated',
          @vdropzone-max-files-exceeded='onMaxFilesExceeded',
          :options='dropzoneOptions')
        button#remove-file-button.btn.btn-default.btn-md(@click='removeFile', :disabled='!hasImageFile || submitted') Remove File
      .col-lg-9
        form.form-horizontal(@submit.prevent='submit')
          .form-group
            label.control-label.col-sm-2 Dataset
            .col-sm-10
              select-dataset(v-model='dataset', :datasets='datasets')
          .form-group
            label.control-label.col-sm-2 Filename
            .col-sm-10
              input.form-control(v-model='filename', type='text', readonly)
          .form-group
            label.control-label.col-sm-2 Electronic Signature
            .col-sm-10
              input.form-control(placeholder='Enter your name', v-model.trim='signature', type='text')
          .form-group
            label.control-label.col-sm-2 Age
            .col-sm-10
              input.form-control(v-model.number='age', type='number', min='0')
          .form-group
            label.control-label.col-sm-2 Sex
            .col-sm-10
              select.form-control(v-model='sex')
                option(selected, disabled, hidden, value='null')
                option(v-for='option in options.sex', :value='option.value') {{ option.description }}
          .form-group
            label.control-label.col-sm-2 Image Type
            .col-sm-10
              select.form-control(v-model='imageType')
                option(selected, disabled, hidden, value='null')
                option(v-for='option in options.imageType', :value='option.value') {{ option.description }}
          .form-group
            label.control-label.col-sm-2 Dermoscopic Type
            .col-sm-10
              select.form-control(v-model='dermoscopicType', :disabled='!dermoscopicImage')
                option(selected, disabled, hidden, value='null')
                option(v-for='option in options.dermoscopicType', :value='option.value') {{ option.description }}
          .form-group
            label.control-label.col-sm-2 Dx Confirm Type
            .col-sm-10
              select.form-control(v-model='dxConfirmType')
                option(selected, disabled, hidden, value='null')
                option(v-for='option in options.dxConfirmType', :value='option.value') {{ option.description }}
          .form-group
            label.control-label.col-sm-2 Diagnosis
            .col-sm-10
              select.form-control(v-model='diagnosis')
                option(selected, disabled, hidden, value='null')
                option(v-for='option in options.diagnosis', :value='option.value') {{ option.description }}
          .form-group
            label.control-label.col-sm-2 Benign/Malignant
            .col-sm-10
              select.form-control(v-model='benignMalignant', :disabled='melanoma')
                option(selected, disabled, hidden, value='null')
                option(v-for='option in options.benignMalignant', :value='option.value') {{ option.description }}
          .form-group
            label.control-label.col-sm-2 Melanocytic
            .col-sm-10
              select.form-control(v-model='melanocytic', disabled, title='Inferred from diagnosis')
                option(selected, disabled, hidden, value='null')
                option(v-for='option in options.melanocytic', :value='option.value') {{ option.description }}
          .form-group
            label.control-label.col-sm-2 Nevus Type
            .col-sm-10
              select.form-control(v-model='nevusType', :disabled='!nevus')
                option(selected, disabled, hidden, value='null')
                option(v-for='option in options.nevusType', :value='option.value') {{ option.description }}
          .form-group
            label.control-label.col-sm-2 Clinical Size (mm)
            .col-sm-10
              input.form-control(v-model.number='clinicalSize', type='number', min='0', step='0.1')
          .form-group
            label.control-label.col-sm-2 Family History of Melanoma
            .col-sm-10
              select.form-control(v-model='familyHistoryOfMelanoma')
                option(selected, disabled, hidden, value='null')
                option(v-for='option in options.familyHistoryOfMelanoma', :value='option.value') {{ option.description }}
          .form-group
            label.control-label.col-sm-2 Personal History of Melanoma
            .col-sm-10
              select.form-control(v-model='personalHistoryOfMelanoma')
                option(selected, disabled, hidden, value='null')
                option(v-for='option in options.personalHistoryOfMelanoma', :value='option.value') {{ option.description }}
          .row
            .col-lg-12
              h4 Melanoma Type
          .row
            .col-lg-6
              .form-group
                label.control-label.col-sm-4 Melanoma Class
                .col-sm-8
                  select.form-control(v-model='melanomaClass', :disabled='!melanoma')
                    option(selected, disabled, hidden, value='null')
                    option(v-for='option in options.melanomaClass', :value='option.value') {{ option.description }}
              .form-group
                label.control-label.col-sm-4 Mitotic Index
                .col-sm-8
                  select.form-control(v-model='mitoticIndex', :disabled='!melanoma')
                    option(selected, disabled, hidden, value='null')
                    option(v-for='option in options.mitoticIndex', :value='option.value') {{ option.description }}
              .form-group
                label.control-label.col-sm-4 Thickness (mm)
                .col-sm-8
                  input.form-control(v-model.number='melanomaThicknessMm', type='number', min='0', step='0.1', :disabled='!melanoma')
            .col-lg-6
              .form-group
                label.control-label.col-sm-4 Melanoma Type
                .col-sm-8
                  select.form-control(v-model='melanomaType', :disabled='!melanoma')
                    option(selected, disabled, hidden, value='null')
                    option(v-for='option in options.melanomaType', :value='option.value') {{ option.description }}
              .form-group
                label.control-label.col-sm-4 Ulcer
                .col-sm-8
                  select.form-control(v-model='melanomaUlcer', :disabled='!melanoma')
                    option(selected, disabled, hidden, value='null')
                    option(v-for='option in options.melanomaUlcer', :value='option.value') {{ option.description }}
          .row
            .col-lg-10
            .col-lg-2
              button.btn.btn-primary.btn-md.pull-right Submit
</template>

<script>
import _ from 'underscore';
import vue2Dropzone from 'vue2-dropzone';
import 'vue2-dropzone/dist/vue2Dropzone.css';

import router from '../router';
import {showAlertDialog} from '../common/utilities';

import SelectDataset from './SelectDataset.vue';
import ImageModel from '../models/ImageModel';

export default {
    components: {
        // TODO: global component registration?
        SelectDataset: SelectDataset,
        vueDropzone: vue2Dropzone
    },
    props: {
        datasets: {
            type: Array,
            required: true
        }
    },
    data: function () {
        return {
            // Image data
            image: null,
            dataset: null,
            filename: null,
            signature: null,
            age: null,
            sex: null,
            imageType: null,
            dermoscopicTypeRaw: null,
            dxConfirmTypeRaw: null,
            diagnosis: null,
            benignMalignantRaw: null,
            nevusTypeRaw: null,
            clinicalSize: null,
            familyHistoryOfMelanoma: null,
            personalHistoryOfMelanoma: null,
            melanomaClassRaw: null,
            mitoticIndexRaw: null,
            melanomaThicknessMmRaw: null,
            melanomaTypeRaw: null,
            melanomaUlcerRaw: null,

            // Interaction state
            submitted: false,

            // Contents of select elements
            options: {
                sex: [
                    {value: 'male', description: 'Male'},
                    {value: 'female', description: 'Female'},
                    {value: 'unknown', description: 'Unknown'}
                ],
                imageType: [
                    {value: 'dermoscopic', description: 'Dermoscopic'},
                    {value: 'clinical', description: 'Clinical'},
                    {value: 'overview', description: 'Overview'},
                    {value: 'unknown', description: 'Unknown'}
                ],
                dermoscopicType: [
                    {value: 'contact polarized', description: 'Contact Polarized'},
                    {value: 'contact non-polarized', description: 'Contact Non-polarized'},
                    {value: 'non-contact polarized', description: 'Non-contact Polarized'},
                    {value: 'unknown', description: 'Unknown'}
                ],
                dxConfirmType: [
                    {value: 'histopathology', description: 'Histopathology'},
                    {value: 'serial imaging showing no change', description: 'Serial Imaging Showing No Change'},
                    {value: 'single image expert consensus', description: 'Expert Consensus (3 raters)'},
                    {value: 'unknown', description: 'Unknown'}
                ],
                diagnosis: [
                    {value: 'atypical melanocytic proliferation', description: 'AMP'},
                    {value: 'AIMP', description: 'AIMP'},
                    {value: 'melanoma', description: 'Melanoma'},
                    {value: 'nevus', description: 'Nevus'},
                    {value: 'other', description: 'Other'},
                    {value: 'unknown', description: 'Unknown'}
                ],
                benignMalignant: [
                    {value: 'benign', description: 'Benign'},
                    {value: 'malignant', description: 'Malignant'},
                    {value: 'indeterminate', description: 'Indeterminate'},
                    {value: 'indeterminate/benign', description: 'Indeterminate favoring benign'},
                    {value: 'indeterminate/malignant', description: 'Indeterminate favoring malignant'},
                    {value: 'unknown', description: 'Unknown'}
                ],
                melanocytic: [
                    {value: 'true', description: 'Yes'},
                    {value: 'false', description: 'No'},
                    {value: 'unknown', description: 'Unknown'}
                ],
                nevusType: [
                    {value: 'blue', description: 'Blue'},
                    {value: 'combined', description: 'Combined'},
                    {value: 'nevus NOS', description: 'Nevus NOS'},
                    {value: 'deep penetrating', description: 'Deep Penetrating'},
                    {value: 'halo', description: 'Halo'},
                    {value: 'persistent/recurrent', description: 'Persistent/Recurrent'},
                    {value: 'pigmented spindle cell of reed', description: 'Pigmented Spindle Cell of Reed'},
                    {value: 'plexiform spindle cell', description: 'Plexiform Spindle Cell'},
                    {value: 'special site', description: 'Special Site'},
                    {value: 'spitz', description: 'Spitz'},
                    {value: 'unknown', description: 'Unknown'}
                ],
                familyHistoryOfMelanoma: [
                    {value: 'true', description: 'Yes'},
                    {value: 'false', description: 'No'},
                    {value: 'unknown', description: 'Unknown'}
                ],
                personalHistoryOfMelanoma: [
                    {value: 'true', description: 'Yes'},
                    {value: 'false', description: 'No'},
                    {value: 'unknown', description: 'Unknown'}
                ],
                melanomaClass: [
                    {value: 'melanoma in situ', description: 'Melanoma In Situ'},
                    {value: 'invasive melanoma', description: 'Invasive Melanoma'},
                    {value: 'recurrent/persistent melanoma, in situ', description: 'Recurrent/persistent melanoma, In Situ'},
                    {value: 'recurrent/persistent melanoma, invasive', description: 'Recurrent/persistent melanoma, Invasive'},
                    {value: 'melanoma NOS', description: 'Melanoma NOS'},
                    {value: 'unknown', description: 'Unknown'}
                ],
                mitoticIndex: [
                    {value: '0/mm^2', description: '0/mm^2'},
                    {value: '<1/mm^2', description: '<1/mm^2'},
                    {value: '1/mm^2', description: '1/mm^2'},
                    {value: '2/mm^2', description: '2/mm^2'},
                    {value: '3/mm^2', description: '3/mm^2'},
                    {value: '4/mm^2', description: '4/mm^2'},
                    {value: '>4/mm^2', description: '>4/mm^2'},
                    {value: 'unknown', description: 'Unknown'}
                ],
                melanomaType: [
                    {value: 'superficial spreading melanoma', description: 'Superficial Spreading Melanoma'},
                    {value: 'nodular melanoma', description: 'Nodular Melanoma'},
                    {value: 'lentigo maligna melanoma', description: 'Lentigo Maligna Melanoma'},
                    {value: 'acral lentiginous melanoma', description: 'Acral Lentiginous Melanoma'},
                    {value: 'spindle cell features melanoma', description: 'Spindle Cell Features Melanoma'},
                    {value: 'melanoma NOS', description: 'Melanoma NOS'},
                    {value: 'unknown', description: 'Unknown'}
                ],
                melanomaUlcer: [
                    {value: 'true', description: 'Yes'},
                    {value: 'false', description: 'No'},
                    {value: 'unknown', description: 'Unknown'}
                ]
            },

            // Dropzone configuration
            dropzoneOptions: {
                url: '/',
                maxFiles: 1,
                autoProcessQueue: false,
                thumbnailWidth: 250,
                thumbnailHeight: null,
                acceptedFiles: 'image/*',
                dictDefaultMessage: '<i class="icon-upload-cloud" style="font-size: 100px"></i><p>Drop File or Click Here</p>'
            }
        };
    },
    computed: {
        hasImageFile: function () {
            return !_.isEmpty(this.filename);
        },
        dermoscopicImage: function () {
            return this.imageType === 'dermoscopic';
        },
        benignMalignant: {
            get: function () {
                if (this.melanoma) {
                    return 'malignant';
                }
                return this.benignMalignantRaw;
            },
            set: function (newValue) {
                this.benignMalignantRaw = newValue;
            }
        },
        dermoscopicType: {
            get: function () {
                if (!this.dermoscopicImage) {
                    return null;
                }
                return this.dermoscopicTypeRaw;
            },
            set: function (newValue) {
                this.dermoscopicTypeRaw = newValue;
            }
        },
        dxConfirmType: {
            get: function () {
                if (_.contains([
                    'indeterminate/benign',
                    'indeterminate/malignant',
                    'indeterminate',
                    'malignant'],
                this.benignMalignant)) {
                    return 'histopathology';
                }
                return this.dxConfirmTypeRaw;
            },
            set: function (newValue) {
                this.dxConfirmTypeRaw = newValue;
            }
        },
        melanoma: function () {
            return this.diagnosis === 'melanoma';
        },
        nevus: function () {
            return this.diagnosis === 'nevus';
        },
        melanocytic: function () {
            if (!this.diagnosis) {
                return null;
            }
            return _.contains([
                'AIMP',
                'melanoma',
                'nevus'],
            this.diagnosis);
        },
        nevusType: {
            get: function () {
                if (!this.nevus) {
                    return null;
                }
                return this.nevusTypeRaw;
            },
            set: function (newValue) {
                this.nevusTypeRaw = newValue;
            }
        },
        melanomaClass: {
            get: function () {
                if (!this.melanoma) {
                    return null;
                }
                return this.melanomaClassRaw;
            },
            set: function (newValue) {
                this.melanomaClassRaw = newValue;
            }
        },
        mitoticIndex: {
            get: function () {
                if (!this.melanoma) {
                    return null;
                }
                return this.mitoticIndexRaw;
            },
            set: function (newValue) {
                this.mitoticIndexRaw = newValue;
            }
        },
        melanomaThicknessMm: {
            get: function () {
                if (!this.melanoma) {
                    return null;
                }
                if (this.melanomaClass === 'melanoma in situ') {
                    return 0.0;
                }
                return this.melanomaThicknessMmRaw;
            },
            set: function (newValue) {
                this.melanomaThicknessMmRaw = newValue;
            }
        },
        melanomaType: {
            get: function () {
                if (!this.melanoma) {
                    return null;
                }
                return this.melanomaTypeRaw;
            },
            set: function (newValue) {
                this.melanomaTypeRaw = newValue;
            }
        },
        melanomaUlcer: {
            get: function () {
                if (!this.melanoma) {
                    return null;
                }
                return this.melanomaUlcerRaw;
            },
            set: function (newValue) {
                this.melanomaUlcerRaw = newValue;
            }
        }
    },
    watch: {
        nevus: function (newValue) {
            if (newValue) {
                this.benignMalignant = 'benign';
            }
        }
    },
    methods: {
        onFileAdded: function (file) {
            this.filename = file.name;
            this.$refs.imageDropzone.dropzone.emit('complete', file);
        },
        onFileRemoved: function (file) {
            if (this.$refs.imageDropzone.getAcceptedFiles().length === 0) {
                this.filename = null;
            }
        },
        onThumbnailGenerated: function (file, dataUrl) {
            $(file.previewElement).last().find('img').attr({width: '100%'});
        },
        onMaxFilesExceeded: function (file) {
            this.$refs.imageDropzone.removeFile(file);
        },
        removeFile: function () {
            this.$refs.imageDropzone.removeAllFiles();
        },
        uploadImage: function () {
            if (this.image) {
                return $.Deferred().resolve(this.image).promise();
            }
            const imageFile = this.$refs.imageDropzone.getAcceptedFiles()[0];
            return this.dataset.uploadImage(this.filename, this.signature, imageFile)
                .then((resp) => {
                    this.image = new ImageModel({_id: resp['_id']});
                    return this.image;
                });
        },
        applyMetadata: function (image) {
            let metadata = {
                age: this.age,
                sex: this.sex,
                image_type: this.imageType,
                dermoscopic_type: this.dermoscopicType,
                diagnosis_confirm_type: this.dxConfirmType,
                diagnosis: this.diagnosis,
                benign_malignant: this.benignMalignant,
                melanocytic: this.melanocytic,
                nevus_type: this.nevusType,
                clin_size_long_diam_mm: this.clinicalSize,
                family_hx_mm: this.familyHistoryOfMelanoma,
                personal_hx_mm: this.personalHistoryOfMelanoma,
                mel_class: this.melanomaClass,
                mel_mitotic_index: this.mitoticIndex,
                mel_thick_mm: this.melanomaThicknessMm,
                mel_type: this.melanomaType,
                mel_ulcer: this.melanomaUlcer
            };

            // Remove unspecified or not applicable values
            metadata = _.pick(metadata, (value, key, object) => {
                if (_.isNull(value)) {
                    return false;
                }
                return (_.isString(value) && !_.isEmpty(value)) || _.isNumber(value);
            });

            // Add expected units to clinical size
            if (_.has(metadata, 'clin_size_long_diam_mm')) {
                metadata.clin_size_long_diam_mm = `${metadata.clin_size_long_diam_mm} mm`;
            }

            console.log(metadata);

            return image.applyMetadata(metadata, true);
        },
        submit: function (event) {
            // Check required fields
            let missingField = null;
            if (!this.hasImageFile) {
                missingField = 'Image';
            } else if (!this.dataset) {
                missingField = 'Dataset';
            } else if (!this.signature) {
                missingField = 'Electronic signature';
            }

            if (!_.isNull(missingField)) {
                showAlertDialog({
                    text: `<h4>${missingField} is required.</h4>`,
                    escapedHtml: true
                });
                return;
            }

            this.submitted = true;

            // TODO: busy indicator

            this.uploadImage()
                .then((image) => {
                    return this.applyMetadata(image);
                })
                .done((resp) => {
                    const errorStrings = _.pluck(resp['errors'], 'description');
                    if (errorStrings.length > 0) {
                        const errorHtml = errorStrings.join('<li>');
                        showAlertDialog({
                            text: `<h4>Metadata contains errors.</h4><br><ul><li>${errorHtml}</ul>`,
                            escapedHtml: true
                        });
                    } else {
                        showAlertDialog({
                            text: '<h4>Image upload complete.</h4>',
                            escapedHtml: true,
                            callback: () => {
                                router.navigate('', {trigger: true});
                            }
                        });
                    }
                })
                .fail((resp) => {
                    this.submitted = false;

                    showAlertDialog({
                        text: `<h4>Error uploading image</h4><br>${_.escape(resp.responseJSON.message)}`,
                        escapedHtml: true
                    });
                });
        }
    }
};
</script>

<style lang="stylus" scoped>
// FIXME: using vue-loader scoped attribute breaks .dz-preview style below
form
  label
    font-weight normal

#image-dropzone
  border 2px dashed #dddddd
  border-radius 8px
  padding 0

  .dz-preview
    transition none
    &:hover
      .dz-details
        color red
        display none
      .dz-image
        img
          transform none
          filter none

#remove-file-button
  margin-top 10px
</style>
