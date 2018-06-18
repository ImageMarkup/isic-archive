import Backbone from 'backbone';
import $ from 'jquery';
import _ from 'underscore';

import {SORT_DESC} from 'girder/constants';
import {DATE_SECOND, formatDate} from 'girder/misc';
import FileModel from 'girder/models/FileModel';
import {confirm} from 'girder/dialog';

import Collection from '../collections/Collection';
import Model from '../models/Model';
import UserModel from '../models/UserModel';
import View from '../view';
import {showAlertDialog} from '../common/utilities';
import router from '../router';

import ApplyMetadataSelectFilePageTemplate from './applyMetadataSelectFilePage.pug';
import ApplyMetadataPageTemplate from './applyMetadataPage.pug';
import './applyMetadataPage.styl';
import './datasetInfoWidget.styl';
import ApplyMetadataValidationPageTemplate from './applyMetadataValidationPage.pug';
import './applyMetadataValidationPage.styl';

// Model for a metadata file
const MetadataFileModel = Model.extend({
    name: function () {
        let time = formatDate(this.get('time'), DATE_SECOND);
        let fileName = this.get('file').name();
        let userName = this.get('user').name();
        return `${time} \u2014 ${fileName} \u2014 ${userName}`;
    }
});

// Collection of metadata files as returned by of DatasetModel.getRegisteredMetadata()
const MetadataFileCollection = Collection.extend({
    model: MetadataFileModel,

    // Sort in reverse chronological order
    sortField: 'time',
    sortDir: SORT_DESC,

    parse: function (data) {
        _.each(data, (item) => {
            item.file = new FileModel(item.file);
            item.user = new UserModel(item.user);

            // Use file ID as item ID
            item._id = item.file.id;
        });
        return data;
    }
});

// Model for a single metadata error or warning
const MetadataResultModel = Backbone.Model.extend({
    description: function () {
        return this.get('description');
    }
});

// Collection of metadata results, i.e. errors or warnings. The 'field' property
// should be set to the name of the field to parse in the response from the server.
// The list of items in the collection is meaningful only when initialized() is true.
// When the collection is in the process of being populated, pending() is true.
const MetadataResultModelCollection = Backbone.Collection.extend({
    initialize: function (models, options) {
        this._field = options.field;
    },

    model: MetadataResultModel,

    _initialized: false,
    _pending: false,

    parse: function (resp) {
        this._pending = false;
        this._initialized = true;
        return resp[this._field];
    },

    initialized: function () {
        return this._initialized;
    },

    uninitialize: function () {
        this._initialized = false;
        this.reset();
    },

    setPending: function () {
        this._pending = true;
        this.uninitialize();
    },

    pending: function () {
        return this._pending;
    }
});

// View for a collection of metadata files in a select tag.
// When user selects a file, a 'changed' event is triggered
// with the ID of the selected file as a parameter.
const ApplyMetadataSelectFileView = View.extend({
    events: {
        'change': 'fileChanged'
    },

    /**
     * @param {MetadataFileCollection} settings.collection
     */
    initialize: function (settings) {
        this.listenTo(this.collection, 'reset', this.render);
        this.render();
    },

    fileChanged: function () {
        let fileId = this.$('select').val();
        this.trigger('changed', fileId);
    },

    render: function () {
        // Destroy previous select2
        let select = this.$('#isic-apply-metadata-file-select');
        select.select2('destroy');

        this.$el.html(ApplyMetadataSelectFilePageTemplate({
            models: this.collection.toArray()
        }));

        // Set up select box
        let placeholder = 'Select a file...';
        if (!this.collection.isEmpty()) {
            placeholder += ` (${this.collection.length} available)`;
        }
        select = this.$('#isic-apply-metadata-file-select');
        select.select2({
            placeholder: placeholder,
            dropdownParent: this.$el
        });
        select.focus();

        return this;
    }
});

// View to select a registered metadata file, validate the metadata, and save
// the metadata to the dataset if validation is successful.
const ApplyMetadataView = View.extend({
    events: {
        'click #isic-apply-metadata-download-button': function () {
            // Download selected metadata file
            this.dataset.downloadMetadata(this.file.id);
        },

        'click #isic-apply-metadata-validate-button': function () {
            this.setButtonsEnabled(false);
            this.validateMetadata();
        },

        'click #isic-apply-metadata-save': function () {
            // Show confirmation dialog
            confirm({
                text: '<h4>Really save metadata?</h4>',
                escapedHtml: true,
                yesText: 'Save',
                yesClass: 'btn-primary',
                confirmCallback: () => {
                    // Ensure dialog is hidden before continuing. Otherwise,
                    // when validateMetadata() displays its modal alert dialog,
                    // the Bootstrap-created element with class "modal-backdrop"
                    // is erroneously not removed.
                    $('#g-dialog-container').on('hidden.bs.modal', () => {
                        this.saving = true;
                        this.setButtonsEnabled(false);
                        this.validateMetadata();
                    });
                }
            });
        }
    },

    /**
     * @param {DatasetModel} settings.dataset
     */
    initialize: function (settings) {
        this.dataset = settings.dataset;

        // Registered metadata files
        this.files = new MetadataFileCollection();

        // Selected metadata file
        this.file = null;

        // Whether the metadata is in the process of being saved or has been saved
        this.saving = false;
        this.saved = false;

        // Errors and warnings in the selected metadata file
        this.errors = new MetadataResultModelCollection(null, {'field': 'errors'});
        this.warnings = new MetadataResultModelCollection(null, {'field': 'warnings'});

        this.selectFileView = new ApplyMetadataSelectFileView({
            collection: this.files,
            parentView: this
        });

        this.listenTo(this.selectFileView, 'changed', this.fileChanged);

        // Observe only warnings, not errors. This avoids redundant updates, because
        // both collections are always updated when validation is run, and warnings
        // are updated last.
        this.listenTo(this.warnings, 'reset', this.resultsChanged);

        this.dataset
            .getRegisteredMetadata()
            .done((resp) => {
                this.files.reset(resp, {parse: true});
            });

        this.render();
    },

    fileChanged: function (fileId) {
        this.file = this.files.get(fileId);
        this.errors.uninitialize();
        this.warnings.uninitialize();

        // Enable action buttons
        this.$('#isic-apply-metadata-download-button, #isic-apply-metadata-validate-button').girderEnable(true);
    },

    resultsChanged: function () {
        // Render validation container, fading out first if it's already shown
        const container = this.$('.isic-apply-metadata-validation-result-container');
        if (container.length) {
            container.fadeOut('fast', () => {
                this.renderValidationContainer();
            });
            return;
        }

        this.renderValidationContainer();
    },

    render: function () {
        this.$el.html(ApplyMetadataPageTemplate({
            dataset: this.dataset
        }));

        this.selectFileView.setElement(
            this.$('#isic-apply-metadata-select-file-container')).render();

        this.renderValidationContainer();

        return this;
    },

    renderValidationContainer: function () {
        this.$('#isic-apply-metadata-validation-container').html(
            ApplyMetadataValidationPageTemplate({
                errors: this.errors,
                warnings: this.warnings,
                file: this.file,
                saving: this.saving,
                saved: this.saved
            }));

        this.$('.isic-apply-metadata-validation-result-container').fadeIn('fast');

        const allowSave =
            !this.saving &&
            this.errors.initialized() && this.errors.isEmpty();
        this.$('#isic-apply-metadata-save').toggleClass('hidden', !allowSave);

        return this;
    },

    validateMetadata: function () {
        this.errors.setPending();
        this.warnings.setPending();

        this.dataset
            .applyMetadata(this.file.id, this.saving)
            .done((resp) => {
                this.saved = this.saving;

                if (this.saving) {
                    this.errors.reset();
                    this.warnings.reset();
                    showAlertDialog({
                        text: '<h4>Metadata saved.</h4>',
                        escapedHtml: true,
                        callback: () => {
                            router.navigate('', {trigger: true});
                        }
                    });
                } else {
                    this.errors.reset(resp, {parse: true});
                    this.warnings.reset(resp, {parse: true});
                }
            })
            .fail((err) => {
                showAlertDialog({text: `Error: ${err.responseJSON.message}`});
            })
            .always(() => {
                this.saving = false;
                this.setButtonsEnabled(true);
            });
    },

    setButtonsEnabled: function (enabled) {
        this.$('#isic-apply-metadata-validate-button, #isic-apply-metadata-save-button').girderEnable(enabled);
    }
});

export default ApplyMetadataView;
