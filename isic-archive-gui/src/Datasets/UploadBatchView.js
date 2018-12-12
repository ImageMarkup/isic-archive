import _ from 'underscore';

import FolderModel from 'girder/models/FolderModel';
import UploadWidget from 'girder/views/widgets/UploadWidget';
import {getCurrentUser} from 'girder/auth';
import {AccessType} from 'girder/constants';

import {SelectableDatasetCollection} from '../collections/DatasetCollection';
import TermsOfUseWidget from '../common/TermsOfUse/TermsOfUseWidget';
import DatasetModel from '../models/DatasetModel';
import View from '../view';
import {showAlertDialog} from '../common/utilities';
import router from '../router';

import SelectDatasetView from './selectDatasetView';
import UploadBatchTemplate from './uploadBatch.pug';
import './uploadBatch.styl';
import './uploadWidget.styl';

import DatasetInfoWidgetTemplate from './datasetInfoWidget.pug';
import './datasetInfoWidget.styl';

const DatasetInfoWidget = View.extend({
    /**
     * @param {SelectableDatasetCollection} settings.collection
     */
    initialize: function (settings) {
        this.listenTo(this.collection, 'select:one', this.render);
        this.render();
    },

    render: function () {
        const dataset = this.collection.selected;

        this.$el.html(DatasetInfoWidgetTemplate({
            dataset: dataset
        }));

        return this;
    }
});

const UploadBatchView = View.extend({
    events: {
        'click #isic-upload-reset': function (event) {
            this.resetUpload();
        },
        'submit #isic-upload-batch-form': function (event) {
            event.preventDefault();
            this.$('#isic-upload-batch-submit').girderEnable(false);

            // Get file ID of uploaded file
            const uploadedFileId = _.isEmpty(this.uploadedFiles)
                ? null
                : this.uploadedFiles[0].id;

            // If no files have been uploaded, delegate error handling to uploadBatch()
            this.uploadBatch(uploadedFileId);
        }
    },

    initialize: function (settings) {
        this.uploadedFiles = [];
        this.uploadFolder = null;

        this.datasets = new SelectableDatasetCollection();
        this.datasets.pageLimit = Number.MAX_SAFE_INTEGER;

        this.selectDatasetView = new SelectDatasetView({
            collection: this.datasets,
            parentView: this
        });

        this.datasetInfoWidget = new DatasetInfoWidget({
            collection: this.datasets,
            parentView: this
        });

        this.listenTo(this.selectDatasetView, 'changed', this.datasetChanged);

        this.termsOfUseWidget = new TermsOfUseWidget({
            parentView: this
        });

        // Show only datasets for which the user has write access
        this.datasets
            .fetch()
            .done((resp) => {
                this.datasets.reset(
                    _.filter(resp, (dataset) => {
                        return dataset['_accessLevel'] >= AccessType.WRITE;
                    })
                );
            });

        this.render();
    },

    render: function () {
        this.$el.html(UploadBatchTemplate({
            canCreateDataset: DatasetModel.canCreate()
        }));

        this.$('#isic-upload-batch-submit').girderEnable(false);

        if (!this.uploadWidget) {
            this.initializeUploadWidget();
        }
        this.updateUploadWidget();

        this.selectDatasetView.setElement(
            this.$('#isic-upload-batch-select-dataset-container')).render();

        this.datasetInfoWidget.setElement(
            this.$('#isic-upload-batch-dataset-info-widget-container')).render();

        this.termsOfUseWidget.setElement(
            this.$('#isic-terms-of-use-container')).render();

        return this;
    },

    datasetChanged: function (dataset) {
        dataset.select();

        // Enable submit button
        this.$('#isic-upload-batch-submit').girderEnable(true);
    },

    initializeUploadWidget: function () {
        if (this.uploadWidget) {
            this.stopListening(this.uploadWidget);
            this.uploadWidget.destroy();
        }
        this.uploadWidget = new UploadWidget({
            parentView: this,
            modal: false,
            noParent: true,
            title: false,
            overrideStart: true,
            multiFile: false
        });

        this.uploadWidget.setElement(this.$('.isic-upload-widget-container'));

        this.listenTo(this.uploadWidget, 'g:filesChanged', this.filesSelected);
        this.listenTo(this.uploadWidget, 'g:uploadStarted', this.uploadStarted);
        this.listenTo(this.uploadWidget, 'g:uploadFinished', this.uploadFinished);
    },

    filesSelected: function (files) {
        // TODO: could validate based on file extension
    },
    uploadStarted: function (files) {
        // Prepare upload folder in user's home and start upload
        if (this.uploadFolder) {
            // Folder already created
            this.startUpload(this.uploadFolder);
        } else {
            // Create new upload folder with unique name
            this.uploadFolder = new FolderModel({
                name: `isic_dataset_${Date.now()}`,
                parentType: 'user',
                parentId: getCurrentUser().id,
                description: 'ISIC dataset upload'
            });

            this.uploadFolder
                .once('g:saved', () => {
                    this.startUpload(this.uploadFolder);
                })
                .once('g:error', () => {
                    showAlertDialog({
                        text: 'Could not create upload folder.'
                    });
                })
                .save();
        }
    },

    uploadFinished: function (info) {
        this.uploadedFiles = _.map(
            info.files,
            (file) => ({id: file.id, name: file.name})
        );
        this.updateUploadWidget();
    },

    startUpload: function (folder) {
        // Configure upload widget and begin upload
        this.uploadWidget.parentType = 'folder';
        this.uploadWidget.parent = folder;
        this.uploadWidget.uploadNextFile();
    },

    /**
     * Upload batch of images. Delegate all validation to the server.
     * @param [zipFileId] The ID of the .zip file, or null.
     */
    uploadBatch: function (zipFileId) {
        const dataset = this.datasets.selected;
        const signature = this.$('#isic-upload-batch-agreement-signature').val();

        dataset
            .uploadBatch(zipFileId, signature)
            .done(() => {
                showAlertDialog({
                    text: '<h4>Batch successfully uploaded.</h4>',
                    escapedHtml: true,
                    callback: () => {
                        // Navigate to register metadata view
                        router.navigate(
                            `dataset/${dataset.id}/metadata/register`,
                            {trigger: true});
                    }
                });
            })
            .fail((resp) => {
                showAlertDialog({
                    text: `<h4>Error uploading batch</h4><br>${_.escape(resp.responseJSON.message)}`,
                    escapedHtml: true
                });

                this.$('#isic-upload-batch-submit').girderEnable(true);
            });
    },

    updateUploadWidget: function () {
        const filesUploaded = !_.isEmpty(this.uploadedFiles);
        this.$('.isic-upload-widget-container').toggle(!filesUploaded);
        this.$('.isic-upload-reset-container').toggle(filesUploaded);

        this.uploadWidget.render();
        this.$('.isic-upload-list').text(`Uploaded: ${_.pluck(this.uploadedFiles, 'name').join(', ')}`);
    },

    resetUpload: function () {
        // Delete uploaded files
        this.uploadFolder
            .once('g:success', () => {
                this.uploadedFiles = [];
                this.updateUploadWidget();
            })
            .removeContents();
    }
});

export default UploadBatchView;
