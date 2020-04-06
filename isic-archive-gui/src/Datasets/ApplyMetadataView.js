import Backbone from 'backbone';
import $ from 'jquery';
import _ from 'underscore';

import {SORT_DESC} from '@girder/core/constants';
import {DATE_SECOND, formatDate} from '@girder/core/misc';
import FileModel from '@girder/core/models/FileModel';
import {confirm} from '@girder/core/dialog';

import Collection from '../collections/Collection';
import Model from '../models/Model';
import UserModel from '../models/UserModel';
import View from '../view';
import {showAlertDialog} from '../common/utilities';
import router from '../router';
import VueComponentView from '../vueComponentView';
import DatasetInfoWidget from './DatasetInfoWidget.vue';

import ApplyMetadataSelectFilePageTemplate from './applyMetadataSelectFilePage.pug';
import ApplyMetadataPageTemplate from './applyMetadataPage.pug';
import './applyMetadataPage.styl';

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

        'click #isic-apply-metadata-apply-button': function () {
            this.setButtonsEnabled(false);
            this.applyMetadata();
        },
    },

    /**
     * @param {DatasetModel} settings.dataset
     */
    initialize: function (settings) {
        this.dataset = settings.dataset;
        this.datasetInfoWidget = null;

        // Registered metadata files
        this.files = new MetadataFileCollection();

        // Selected metadata file
        this.file = null;

        // Whether the metadata is in the process of being saved or has been saved
        this.saving = false;
        this.saved = false;

        this.selectFileView = new ApplyMetadataSelectFileView({
            collection: this.files,
            parentView: this
        });

        this.listenTo(this.selectFileView, 'changed', this.fileChanged);

        this.dataset
            .getRegisteredMetadata()
            .done((resp) => {
                this.files.reset(resp, {parse: true});
            });

        this.render();
    },

    fileChanged: function (fileId) {
        this.file = this.files.get(fileId);

        // Enable action buttons
        this.$('#isic-apply-metadata-download-button, #isic-apply-metadata-apply-button').girderEnable(true);
    },

    render: function () {
        this.$el.html(ApplyMetadataPageTemplate());
        this.datasetInfoWidget = new VueComponentView({
            el: this.$('.isic-dataset-info-widget'),
            component: DatasetInfoWidget,
            props: {
                dataset: this.dataset,
            },
            parentView: this
        });

        this.selectFileView.setElement(
            this.$('#isic-apply-metadata-select-file-container')).render();

        return this;
    },

    applyMetadata: function () {
        this.dataset
            .applyMetadata(this.file.id, this.saving)
            .done((resp) => {
                this.saved = this.saving;

                if (this.saving) {
                    showAlertDialog({
                        text: '<h4>Metadata applying.</h4>',
                        escapedHtml: true,
                        callback: () => {
                            router.navigate('', {trigger: true});
                        }
                    });
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
        this.$('#isic-apply-metadata-apply-button').girderEnable(enabled);
    }
});

export default ApplyMetadataView;
