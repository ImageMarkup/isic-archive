<template lang="pug">
.isic-upload-image-container
  .container
    .row
      .col-lg-12
        h2 Upload image to dataset
    .row
      .col-lg-3
        FileSelect(v-model='imageFile', accept='image/*', thumbnail)
      .col-lg-9
        form.form-horizontal(@submit.prevent='submit')
          .form-group
            label.control-label.col-sm-2 Dataset
            .col-sm-10
              SelectDataset(v-model='dataset', :accessLevel='AccessType.WRITE')
          .form-group
            label.control-label.col-sm-2 Filename
            .col-sm-10
              input.form-control(:value='imageFile ? imageFile.name: ""', type='text', readonly)
          .form-group
            label.control-label.col-sm-2 Electronic Signature
            .col-sm-10
              input.form-control(
                placeholder='Enter your name', v-model.trim='signature', type='text')
          .form-group
            label.control-label.col-sm-2 Age
            .col-sm-10
              input.form-control(v-model.number='age', type='number', min='0')
          .form-group
            label.control-label.col-sm-2 Sex
            .col-sm-10
              select.form-control(v-model='sex')
                option(selected, disabled, hidden, value='null')
                option(
                  v-for='option in options.sex', :value='option.value') {{ option.description }}
          .form-group
            label.control-label.col-sm-2 Image Type
            .col-sm-10
              select.form-control(v-model='imageType')
                option(selected, disabled, hidden, value='null')
                option(
                  v-for='option in options.imageType',
                  :value='option.value') {{ option.description }}
          .form-group
            label.control-label.col-sm-2 Dermoscopic Type
            .col-sm-10
              select.form-control(v-model='dermoscopicType', :disabled='!dermoscopicImage')
                option(selected, disabled, hidden, value='null')
                option(
                  v-for='option in options.dermoscopicType',
                  :value='option.value') {{ option.description }}
          .form-group
            label.control-label.col-sm-2 Dx Confirm Type
            .col-sm-10
              select.form-control(v-model='dxConfirmType')
                option(selected, disabled, hidden, value='null')
                option(
                  v-for='option in options.dxConfirmType',
                  :value='option.value') {{ option.description }}
          .form-group
            label.control-label.col-sm-2 Diagnosis
            .col-sm-10
              select.form-control(v-model='diagnosis')
                option(selected, disabled, hidden, value='null')
                option(
                  v-for='option in options.diagnosis',
                  :value='option.value') {{ option.description }}
          .form-group
            label.control-label.col-sm-2 Benign/Malignant
            .col-sm-10
              select.form-control(v-model='benignMalignant', :disabled='melanoma')
                option(selected, disabled, hidden, value='null')
                option(
                  v-for='option in options.benignMalignant',
                  :value='option.value') {{ option.description }}
          .form-group
            label.control-label.col-sm-2 Melanocytic
            .col-sm-10
              select.form-control(
                v-model='melanocytic', :disabled='forceMelanocyticValue',
                :title='forceMelanocyticValue ? \'Inferred from diagnosis\' : null')
                option(selected, disabled, hidden, value='null')
                option(
                  v-for='option in options.melanocytic',
                  :value='option.value') {{ option.description }}
          .form-group
            label.control-label.col-sm-2 Nevus Type
            .col-sm-10
              select.form-control(v-model='nevusType', :disabled='!nevus')
                option(selected, disabled, hidden, value='null')
                option(
                  v-for='option in options.nevusType',
                  :value='option.value') {{ option.description }}
          .form-group
            label.control-label.col-sm-2 Clinical Size (mm)
            .col-sm-10
              input.form-control(v-model.number='clinicalSize', type='number', min='0', step='0.1')
          .form-group
            label.control-label.col-sm-2 Family History of Melanoma
            .col-sm-10
              select.form-control(v-model='familyHistoryOfMelanoma')
                option(selected, disabled, hidden, value='null')
                option(
                  v-for='option in options.familyHistoryOfMelanoma',
                  :value='option.value') {{ option.description }}
          .form-group
            label.control-label.col-sm-2 Personal History of Melanoma
            .col-sm-10
              select.form-control(v-model='personalHistoryOfMelanoma')
                option(selected, disabled, hidden, value='null')
                option(
                  v-for='option in options.personalHistoryOfMelanoma',
                  :value='option.value') {{ option.description }}
          .form-group
            label.control-label.col-sm-2 General Anatomic Site
            .col-sm-10
              select.form-control(v-model='anatomSiteGeneral')
                option(selected, disabled, hidden, value='null')
                option(
                  v-for='option in options.anatomSiteGeneral',
                  :value='option.value') {{ option.description }}
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
                    option(
                      v-for='option in options.melanomaClass',
                      :value='option.value') {{ option.description }}
              .form-group
                label.control-label.col-sm-4 Mitotic Index
                .col-sm-8
                  select.form-control(v-model='mitoticIndex', :disabled='!melanoma')
                    option(selected, disabled, hidden, value='null')
                    option(
                      v-for='option in options.mitoticIndex',
                      :value='option.value') {{ option.description }}
              .form-group
                label.control-label.col-sm-4 Thickness (mm)
                .col-sm-8
                  input.form-control(
                    v-model.number='melanomaThicknessMm', type='number', min='0', step='0.1',
                    :disabled='!melanoma')
            .col-lg-6
              .form-group
                label.control-label.col-sm-4 Melanoma Type
                .col-sm-8
                  select.form-control(v-model='melanomaType', :disabled='!melanoma')
                    option(selected, disabled, hidden, value='null')
                    option(
                      v-for='option in options.melanomaType',
                      :value='option.value') {{ option.description }}
              .form-group
                label.control-label.col-sm-4 Ulcer
                .col-sm-8
                  select.form-control(v-model='melanomaUlcer', :disabled='!melanoma')
                    option(selected, disabled, hidden, value='null')
                    option(
                      v-for='option in options.melanomaUlcer',
                      :value='option.value') {{ option.description }}
          .row
            .col-lg-10
            .col-lg-2
              button.btn.btn-primary.btn-md.pull-right Submit
</template>

<script>
import $ from 'jquery';
import _ from 'underscore';

import { AccessType } from '@girder/core/constants';

import router from '../router';
import { showAlertDialog } from '../common/utilities';

import FileSelect from './FileSelect.vue';
import ImageModel from '../models/ImageModel';
import SelectDataset from './SelectDataset.vue';

export default {
  components: {
    FileSelect,
    SelectDataset,
  },
  data() {
    return {
      // Image data
      imageFile: null,
      image: null,
      dataset: null,
      signature: null,
      age: null,
      sex: null,
      imageType: null,
      dermoscopicTypeRaw: null,
      dxConfirmTypeRaw: null,
      diagnosis: null,
      benignMalignantRaw: null,
      melanocyticRaw: null,
      nevusTypeRaw: null,
      clinicalSize: null,
      familyHistoryOfMelanoma: null,
      personalHistoryOfMelanoma: null,
      melanomaClassRaw: null,
      mitoticIndexRaw: null,
      melanomaThicknessMmRaw: null,
      melanomaTypeRaw: null,
      melanomaUlcerRaw: null,
      anatomSiteGeneral: null,

      // Interaction state
      submitted: false,

      // Contents of select elements
      options: {
        sex: [
          { value: 'male', description: 'Male' },
          { value: 'female', description: 'Female' },
          { value: 'unknown', description: 'Unknown' },
        ],
        imageType: [
          { value: 'dermoscopic', description: 'Dermoscopic' },
          { value: 'clinical', description: 'Clinical' },
          { value: 'overview', description: 'Overview' },
          { value: 'unknown', description: 'Unknown' },
        ],
        dermoscopicType: [
          { value: 'contact polarized', description: 'Contact Polarized' },
          { value: 'contact non-polarized', description: 'Contact Non-polarized' },
          { value: 'non-contact polarized', description: 'Non-contact Polarized' },
          { value: 'unknown', description: 'Unknown' },
        ],
        dxConfirmType: [
          { value: 'histopathology', description: 'Histopathology' },
          {
            value: 'serial imaging showing no change',
            description: 'Serial Imaging Showing No Change',
          },
          { value: 'single image expert consensus', description: 'Expert Consensus (3 raters)' },
          {
            value: 'confocal microscopy with consensus dermoscopy',
            description: 'Confocal Microscopy with Consensus Dermoscopy',
          },
          { value: 'unknown', description: 'Unknown' },
        ],
        diagnosis: [
          { value: 'AIMP', description: 'AIMP', melanocytic: true },
          { value: 'atypical melanocytic proliferation', description: 'AMP', melanocytic: true },
          { value: 'acrochordon', description: 'Acrochordon', melanocytic: false },
          { value: 'actinic keratosis', description: 'Actinic Keratosis', melanocytic: false },
          { value: 'adnexal tumor', description: 'Adnexal Tumor', melanocytic: false },
          {
            value: 'angiofibroma or fibrous papule',
            description: 'Angiofibroma or Fibrous Papule',
            melanocytic: false,
          },
          { value: 'angiokeratoma', description: 'Angiokeratoma', melanocytic: false },
          { value: 'angioma', description: 'Angioma', melanocytic: false },
          { value: 'atypical spitz tumor', description: 'Atypical Spitz Tumor', melanocytic: false },
          { value: 'basal cell carcinoma', description: 'Basal Cell Carcinoma', melanocytic: false },
          { value: 'cafe-au-lait macule', description: 'Café-au-Lait Macule', melanocytic: false },
          { value: 'clear cell acanthoma', description: 'Clear Cell Acanthoma', melanocytic: false },
          { value: 'dermatofibroma', description: 'Dermatofibroma', melanocytic: false },
          { value: 'ephelis', description: 'Ephelis', melanocytic: false },
          { value: 'epidermal nevus', description: 'Epidermal Nevus', melanocytic: false },
          { value: 'lentigo NOS', description: 'Lentigo NOS', melanocytic: true },
          { value: 'lentigo simplex', description: 'Lentigo Simplex', melanocytic: true },
          { value: 'lichenoid keratosis', description: 'Lichenoid Keratosis', melanocytic: false },
          { value: 'melanoma', description: 'Melanoma', melanocytic: true },
          { value: 'melanoma metastasis', description: 'Melanoma Metastasis', melanocytic: true },
          { value: 'merkel cell carcinoma', description: 'Merkel Cell Carcinoma', melanocytic: false },
          { value: 'mucosal melanosis', description: 'Mucosal Melanosis', melanocytic: false },
          { value: 'neurofibroma', description: 'Neurofibroma', melanocytic: false },
          { value: 'nevus', description: 'Nevus', melanocytic: true },
          { value: 'nevus spilus', description: 'Nevus Spilus', melanocytic: true },
          { value: 'pyogenic granuloma', description: 'Pyogenic Granuloma', melanocytic: false },
          { value: 'scar', description: 'Scar', melanocytic: false },
          { value: 'sebaceous adenoma', description: 'Sebaceous Adenoma', melanocytic: false },
          { value: 'sebaceous hyperplasia', description: 'Sebaceous Hyperplasia', melanocytic: false },
          { value: 'seborrheic keratosis', description: 'Seborrheic Keratosis', melanocytic: false },
          { value: 'solar lentigo', description: 'Solar Lentigo', melanocytic: true },
          { value: 'squamous cell carcinoma', description: 'Squamous Cell Carcinoma', melanocytic: false },
          { value: 'verruca', description: 'Verruca', melanocytic: false },
          { value: 'pigmented benign keratosis', description: 'Pigmented Benign Keratosis', melanocytic: false },
          { value: 'vascular lesion', description: 'Vascular Lesion', melanocytic: false },
          { value: 'other', description: 'Other', melanocytic: null },
          { value: 'unknown', description: 'Unknown', melanocytic: null },
        ],
        benignMalignant: [
          { value: 'benign', description: 'Benign' },
          { value: 'malignant', description: 'Malignant' },
          { value: 'indeterminate', description: 'Indeterminate' },
          { value: 'indeterminate/benign', description: 'Indeterminate favoring benign' },
          { value: 'indeterminate/malignant', description: 'Indeterminate favoring malignant' },
          { value: 'unknown', description: 'Unknown' },
        ],
        melanocytic: [
          { value: 'true', description: 'Yes' },
          { value: 'false', description: 'No' },
          { value: 'unknown', description: 'Unknown' },
        ],
        nevusType: [
          { value: 'blue', description: 'Blue' },
          { value: 'combined', description: 'Combined' },
          { value: 'nevus NOS', description: 'Nevus NOS' },
          { value: 'deep penetrating', description: 'Deep Penetrating' },
          { value: 'halo', description: 'Halo' },
          { value: 'persistent/recurrent', description: 'Persistent/Recurrent' },
          { value: 'pigmented spindle cell of reed', description: 'Pigmented Spindle Cell of Reed' },
          { value: 'plexiform spindle cell', description: 'Plexiform Spindle Cell' },
          { value: 'special site', description: 'Special Site' },
          { value: 'spitz', description: 'Spitz' },
          { value: 'unknown', description: 'Unknown' },
        ],
        familyHistoryOfMelanoma: [
          { value: 'true', description: 'Yes' },
          { value: 'false', description: 'No' },
          { value: 'unknown', description: 'Unknown' },
        ],
        personalHistoryOfMelanoma: [
          { value: 'true', description: 'Yes' },
          { value: 'false', description: 'No' },
          { value: 'unknown', description: 'Unknown' },
        ],
        melanomaClass: [
          { value: 'melanoma in situ', description: 'Melanoma In Situ' },
          { value: 'invasive melanoma', description: 'Invasive Melanoma' },
          { value: 'recurrent/persistent melanoma, in situ', description: 'Recurrent/persistent melanoma, In Situ' },
          { value: 'recurrent/persistent melanoma, invasive', description: 'Recurrent/persistent melanoma, Invasive' },
          { value: 'melanoma NOS', description: 'Melanoma NOS' },
          { value: 'unknown', description: 'Unknown' },
        ],
        mitoticIndex: [
          { value: '0/mm^2', description: '0/mm^2' },
          { value: '<1/mm^2', description: '<1/mm^2' },
          { value: '1/mm^2', description: '1/mm^2' },
          { value: '2/mm^2', description: '2/mm^2' },
          { value: '3/mm^2', description: '3/mm^2' },
          { value: '4/mm^2', description: '4/mm^2' },
          { value: '>4/mm^2', description: '>4/mm^2' },
          { value: 'unknown', description: 'Unknown' },
        ],
        melanomaType: [
          { value: 'superficial spreading melanoma', description: 'Superficial Spreading Melanoma' },
          { value: 'nodular melanoma', description: 'Nodular Melanoma' },
          { value: 'lentigo maligna melanoma', description: 'Lentigo Maligna Melanoma' },
          { value: 'acral lentiginous melanoma', description: 'Acral Lentiginous Melanoma' },
          { value: 'spindle cell features melanoma', description: 'Spindle Cell Features Melanoma' },
          { value: 'melanoma NOS', description: 'Melanoma NOS' },
          { value: 'unknown', description: 'Unknown' },
        ],
        melanomaUlcer: [
          { value: 'true', description: 'Yes' },
          { value: 'false', description: 'No' },
          { value: 'unknown', description: 'Unknown' },
        ],
        anatomSiteGeneral: [
          { value: 'head/neck', description: 'Head/Neck' },
          { value: 'upper extremity', description: 'Upper Extremity' },
          { value: 'lower extremity', description: 'Lower Extremity' },
          { value: 'anterior torso', description: 'Anterior Torso' },
          { value: 'posterior torso', description: 'Posterior Torso' },
          { value: 'palms/soles', description: 'Palms/Soles' },
          { value: 'lateral torso', description: 'Lateral Torso' },
          { value: 'oral/genital', description: 'Genitalia' },
          { value: 'unknown', description: 'Unknown' },
        ],
      },

      // Constants
      AccessType,
    };
  },
  computed: {
    dermoscopicImage() {
      return this.imageType === 'dermoscopic';
    },
    benignMalignant: {
      get() {
        if (this.melanoma) {
          return 'malignant';
        }
        return this.benignMalignantRaw;
      },
      set(newValue) {
        this.benignMalignantRaw = newValue;
      },
    },
    dermoscopicType: {
      get() {
        if (!this.dermoscopicImage) {
          return null;
        }
        return this.dermoscopicTypeRaw;
      },
      set(newValue) {
        this.dermoscopicTypeRaw = newValue;
      },
    },
    dxConfirmType: {
      get() {
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
      set(newValue) {
        this.dxConfirmTypeRaw = newValue;
      },
    },
    melanoma() {
      return this.diagnosis === 'melanoma';
    },
    nevus() {
      return this.diagnosis === 'nevus' || this.diagnosis === 'nevus spilus';
    },
    forceMelanocyticValue() {
      const diagnosis = _.findWhere(this.options.diagnosis, { value: this.diagnosis });
      return diagnosis ? !_.isNull(diagnosis.melanocytic) : false;
    },
    melanocytic: {
      get() {
        const diagnosis = _.findWhere(this.options.diagnosis, { value: this.diagnosis });
        if (diagnosis && !_.isNull(diagnosis.melanocytic)) {
          return diagnosis.melanocytic;
        }
        return this.melanocyticRaw;
      },
      set(newValue) {
        this.melanocyticRaw = newValue;
      },
    },
    nevusType: {
      get() {
        if (!this.nevus) {
          return null;
        }
        return this.nevusTypeRaw;
      },
      set(newValue) {
        this.nevusTypeRaw = newValue;
      },
    },
    melanomaClass: {
      get() {
        if (!this.melanoma) {
          return null;
        }
        return this.melanomaClassRaw;
      },
      set(newValue) {
        this.melanomaClassRaw = newValue;
      },
    },
    mitoticIndex: {
      get() {
        if (!this.melanoma) {
          return null;
        }
        return this.mitoticIndexRaw;
      },
      set(newValue) {
        this.mitoticIndexRaw = newValue;
      },
    },
    melanomaThicknessMm: {
      get() {
        if (!this.melanoma) {
          return null;
        }
        if (this.melanomaClass === 'melanoma in situ') {
          return 0.0;
        }
        return this.melanomaThicknessMmRaw;
      },
      set(newValue) {
        this.melanomaThicknessMmRaw = newValue;
      },
    },
    melanomaType: {
      get() {
        if (!this.melanoma) {
          return null;
        }
        return this.melanomaTypeRaw;
      },
      set(newValue) {
        this.melanomaTypeRaw = newValue;
      },
    },
    melanomaUlcer: {
      get() {
        if (!this.melanoma) {
          return null;
        }
        return this.melanomaUlcerRaw;
      },
      set(newValue) {
        this.melanomaUlcerRaw = newValue;
      },
    },
  },
  methods: {
    uploadImage() {
      if (this.image) {
        return $.Deferred().resolve(this.image).promise();
      }
      return this.dataset.uploadImage(this.imageFile.name, this.signature, this.imageFile)
        .then((resp) => {
          this.image = new ImageModel({ _id: resp._id });
          return this.image;
        });
    },
    applyMetadata(image) {
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
        mel_ulcer: this.melanomaUlcer,
        anatom_site_general: this.anatomSiteGeneral,
      };

      // Remove unspecified or not applicable values
      metadata = _.pick(metadata, (value) => {
        if (_.isNull(value)) {
          return false;
        }
        return (_.isString(value) && !_.isEmpty(value)) || _.isNumber(value);
      });

      // Add expected units to clinical size
      if (_.has(metadata, 'clin_size_long_diam_mm')) {
        metadata.clin_size_long_diam_mm = `${metadata.clin_size_long_diam_mm} mm`;
      }

      return image.applyMetadata(metadata, true);
    },
    submit() {
      // Check required fields
      let missingField = null;
      if (!this.imageFile) {
        missingField = 'Image';
      } else if (!this.dataset) {
        missingField = 'Dataset';
      } else if (!this.signature) {
        missingField = 'Electronic signature';
      }

      if (!_.isNull(missingField)) {
        showAlertDialog({
          text: `<h4>${missingField} is required.</h4>`,
          escapedHtml: true,
        });
        return;
      }

      this.submitted = true;

      // TODO: busy indicator

      this.uploadImage()
        .then((image) => this.applyMetadata(image))
        .done((resp) => {
          const errorStrings = _.pluck(resp.errors, 'description');
          if (errorStrings.length > 0) {
            const errorHtml = errorStrings.join('<li>');
            showAlertDialog({
              text: `<h4>Metadata contains errors.</h4><br><ul><li>${errorHtml}</ul>`,
              escapedHtml: true,
            });
          } else {
            showAlertDialog({
              text: '<h4>Image upload complete.</h4>',
              escapedHtml: true,
              callback: () => {
                router.navigate('', { trigger: true });
              },
            });
          }
        })
        .fail((resp) => {
          this.submitted = false;

          showAlertDialog({
            text: `<h4>Error uploading image</h4><br>${_.escape(resp.responseJSON.message)}`,
            escapedHtml: true,
          });
        });
    },
  },
};
</script>

<style lang="stylus" scoped>
form
  label
    font-weight normal
</style>
