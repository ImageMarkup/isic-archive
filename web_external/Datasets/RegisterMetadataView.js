import _ from 'underscore';

import FolderModel from 'girder/models/FolderModel';
import UploadWidget from 'girder/views/widgets/UploadWidget';
import {getCurrentUser} from 'girder/auth';

import View from '../view';
import {showAlertDialog} from '../common/utilities';
import router from '../router';

import RegisterMetadataTemplate from './registerMetadata.pug';
import './registerMetadata.styl';
import './datasetInfoWidget.styl';
import './uploadWidget.styl';

const RegisterMetadataView = View.extend({
    events: {
        'click #isic-upload-reset': function (event) {
            this.resetUpload();
        },
        'click #isic-register-metadata-submit': function (event) {
            const uploadedFileId = _.isEmpty(this.uploadedFiles)
                ? null
                : this.uploadedFiles[0].id;

            if (uploadedFileId) {
                this.$('#isic-register-metadata-submit').girderEnable(false);

                this.registerMetadata(uploadedFileId);
            } else {
                // Require CSV file to be uploaded
                showAlertDialog({ text: 'Please upload a CSV file.' });
            }
        }
    },

    /**
     * @param {DatasetModel} settings.dataset
     */
    initialize: function (settings) {
        this.dataset = settings.dataset;

        this.uploadedFiles = [];
        this.uploadFolder = null;

        this.listenTo(this.dataset, 'isic:registerMetadata:success', () => {
            showAlertDialog({
                text: '<h4>Metadata successfully registered.</h4><br>' +
                      'An administrator may contact you via email.',
                escapedHtml: true,
                callback: () => {
                    router.navigate('', {trigger: true});
                }
            });
        });

        this.listenTo(this.dataset, 'isic:registerMetadata:error', (resp) => {
            showAlertDialog({
                text: `<h4>Error registering metadata</h4><br>${_.escape(resp.responseJSON.message)}`,
                escapedHtml: true
            });
            this.$('#isic-register-metadata-submit').girderEnable(true);
        });

        this.render();
    },

    render: function () {
        this.$el.html(RegisterMetadataTemplate({
            dataset: this.dataset
        }));

        if (!this.uploadWidget) {
            this.initializeUploadWidget();
        }
        this.updateUploadWidget();

        return this;
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
                name: `isic_metadata_${Date.now()}`,
                parentType: 'user',
                parentId: getCurrentUser().id,
                description: 'ISIC metadata upload'
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
    },

    registerMetadata: function (metadataFileId) {
        this.dataset.registerMetadata(metadataFileId);
    }
});

export default RegisterMetadataView;
