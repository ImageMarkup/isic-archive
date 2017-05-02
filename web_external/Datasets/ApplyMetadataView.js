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

import ApplyMetadataSelectFilePageTemplate from './applyMetadataSelectFilePage.jade';
import ApplyMetadataPageTemplate from './applyMetadataPage.jade';
import './applyMetadataPage.styl';
import './datasetInfoWidget.styl';
import ApplyMetadataValidationPageTemplate from './applyMetadataValidationPage.jade';
import './applyMetadataValidationPage.styl';

// Model for a metadata file
var MetadataFileModel = Model.extend({
    name: function () {
        var time = formatDate(this.get('time'), DATE_SECOND);
        var fileName = this.get('file').name();
        var userName = this.get('user').name();
        return time + ' \u2014 ' + fileName + ' \u2014 ' + userName;
    }
});

// Collection of metadata files as returned by of DatasetModel.getRegisteredMetadata()
var MetadataFileCollection = Collection.extend({
    model: MetadataFileModel,

    // Sort in reverse chronological order
    sortField: 'time',
    sortDir: SORT_DESC,

    parse: function (data) {
        _.each(data, function (item) {
            item.file = new FileModel(item.file);
            item.user = new UserModel(item.user);

            // Use file ID as item ID
            item._id = item.file.id;
        });
        return data;
    }
});

// Model for a single metadata error
var MetadataErrorModel = Backbone.Model.extend({
    description: function () {
        return this.get('description');
    }
});

// Collection of metadata errors. The list of items in the collection is
// meaningful only when initialized() is true.
var MetadataErrorCollection = Backbone.Collection.extend({
    model: MetadataErrorModel,

    _initialized: false,

    parse: function (resp) {
        this._initialized = true;
        return resp.errors;
    },

    initialized: function () {
        return this._initialized;
    },

    uninitialize: function () {
        this._initialized = false;
        this.reset();
    }
});

// View for a collection of metadata files in a select tag.
// When user selects a file, a 'changed' event is triggered
// with the ID of the selected file as a parameter.
var ApplyMetadataSelectFileView = View.extend({
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
        var fileId = this.$('select').val();
        this.trigger('changed', fileId);
    },

    render: function () {
        // Destroy previous select2
        var select = this.$('#isic-apply-metadata-file-select');
        select.select2('destroy');

        this.$el.html(ApplyMetadataSelectFilePageTemplate({
            models: this.collection.models
        }));

        // Set up select box
        var placeholder = 'Select a file...';
        if (!this.collection.isEmpty()) {
            placeholder += ' (' + this.collection.length + ' available)';
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
var ApplyMetadataView = View.extend({
    events: {
        'click #isic-apply-metadata-download-button': function () {
            // Download selected metadata file
            var fileModel = new FileModel({_id: this.file.id});
            fileModel.download();
        },

        'click #isic-apply-metadata-validate-button': function () {
            var save = false;
            this.validateMetadata(save);
        },

        'click #isic-apply-metadata-save': function () {
            // Show confirmation dialog
            confirm({
                text: '<h4>Really save metadata?</h4>',
                escapedHtml: true,
                yesText: 'Save',
                yesClass: 'btn-primary',
                confirmCallback: _.bind(function () {
                    // Ensure dialog is hidden before continuing. Otherwise,
                    // when validateMetadata() displays its modal alert dialog,
                    // the Bootstrap-created element with class "modal-backdrop"
                    // is erroneously not removed.
                    $('#g-dialog-container').on('hidden.bs.modal', _.bind(function () {
                        var save = true;
                        this.validateMetadata(save);
                    }, this));
                }, this)
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

        // Errors in the selected metadata file
        this.errors = new MetadataErrorCollection();

        this.selectFileView = new ApplyMetadataSelectFileView({
            collection: this.files,
            parentView: this
        });

        this.listenTo(this.selectFileView, 'changed', this.fileChanged);
        this.listenTo(this.errors, 'reset', this.errorsChanged);

        this.dataset.getRegisteredMetadata().done(_.bind(function (resp) {
            this.files.reset(resp, {parse: true});
        }, this));

        this.render();
    },

    fileChanged: function (fileId) {
        this.file = this.files.get(fileId);
        this.errors.uninitialize();

        // Enable action buttons
        this.$('#isic-apply-metadata-download-button, #isic-apply-metadata-validate-button').removeAttr('disabled');
    },

    errorsChanged: function () {
        this.renderValidationContainer();

        var allowSave = this.errors.initialized() && this.errors.isEmpty();
        this.$('#isic-apply-metadata-save').toggleClass('hidden', !allowSave);
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
                file: this.file
            }));

        return this;
    },

    validateMetadata: function (save) {
        this.dataset.applyMetadata(this.file.id, save).then(_.bind(function (resp) {
            this.errors.reset(resp, {parse: true});

            if (save) {
                showAlertDialog({
                    text: '<h4>Metadata saved.</h4>',
                    escapedHtml: true,
                    callback: function () {
                        router.navigate('', {trigger: true});
                    }
                });
            }
        }, this), function (err) {
            showAlertDialog({text: 'Error: ' + err.responseJSON.message});
        });
    }
});

export default ApplyMetadataView;
