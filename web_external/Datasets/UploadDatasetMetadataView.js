// View for a collection of datasets in a select tag
isic.views.UploadDatasetMetadataSelectDatasetView = isic.View.extend({
    events: {
        'change': 'datasetChanged'
    },

    initialize: function (options) {
        this.listenTo(this.collection, 'reset', this.render);

        this.render();
    },

    datasetChanged: function () {
        this.trigger('changed', this.$('select').val());
    },

    render: function () {
        // Destroy previous select2
        var select = this.$('#isic-upload-dataset-metadata-dataset-select');
        select.select2('destroy');

        this.$el.html(isic.templates.uploadDatasetMetadataSelectDatasetPage({
            models: this.collection.models
        }));

        // Set up select box
        var placeholder = 'Select a dataset...';
        if (!this.collection.isEmpty()) {
            placeholder += ' (' + this.collection.length + ' available)';
        }
        select = this.$('#isic-upload-dataset-metadata-dataset-select');
        select.select2({
            placeholder: placeholder
        });
        select.focus();

        return this;
    }
});

isic.views.UploadDatasetMetadataView = isic.View.extend({
    events: {
        'click #isic-upload-reset': function (event) {
            this.resetUpload();
        },
        'click #isic-upload-dataset-metadata-submit': function (event) {
            // Require dataset to be selected and CSV file to be uploaded
            var errorMessage = null;
            if (!this.dataset.id) {
                errorMessage = 'Please select a dataset.';
            } else if (_.isEmpty(this.uploadedCsvFiles) || !this.uploadFolder) {
                errorMessage = 'Please upload a CSV file.';
            }

            if (errorMessage !== null) {
                isic.showAlertDialog({ text: errorMessage });
                return;
            }

            this.$('#isic-upload-dataset-metadata-submit').prop('disabled', true);

            // Get file ID of uploaded file, then register metadata
            var items = new isic.collections.ItemCollection();
            items.once('g:changed', function () {
                if (!items.isEmpty()) {
                    var item = items.first();
                    item.once('g:files', function (fileCollection) {
                        var fileId = fileCollection.first().id;
                        this.registerMetadata(fileId);
                    }, this).getFiles();
                } else {
                    this.registerMetadata(null);
                }
            }, this).fetch({
                folderId: this.uploadFolder.id
            });
        }
    },

    initialize: function (settings) {
        this.uploadedCsvFiles = [];
        this.uploadFolder = null;

        this.dataset = new isic.models.DatasetModel();
        this.datasets = new isic.collections.DatasetCollection();

        this.selectDatasetView = new isic.views.UploadDatasetMetadataSelectDatasetView({
            collection: this.datasets,
            parentView: this
        });

        this.datasets.fetch();

        this.listenTo(this.dataset, 'isic:registerMetadata:success', function () {
            isic.showAlertDialog({
                text: '<h4>Metadata successfully registered.</h4><br>' +
                      'An administrator may contact you via email.',
                escapedHtml: true,
                callback: function () {
                    isic.router.navigate('', {trigger: true});
                }
            });
        });

        this.listenTo(this.dataset, 'isic:registerMetadata:error', function (resp) {
            isic.showAlertDialog({
                text: '<h4>Error registering metadata</h4><br>' + resp.responseJSON.message,
                escapedHtml: true
            });
            this.$('#isic-upload-dataset-metadata-submit').prop('disabled', false);
        });

        this.listenTo(this.selectDatasetView, 'changed', this.datasetChanged);

        this.render();
    },

    datasetChanged: function (datasetId) {
        this.dataset.set({'_id': datasetId});
    },

    render: function () {
        this.$el.html(isic.templates.uploadDatasetMetadata({
            user: girder.currentUser
        }));

        this.selectDatasetView.setElement(
            this.$('#isic-upload-dataset-metadata-dataset-select-container')).render();

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
        this.uploadWidget = new girder.views.UploadWidget({
            parentView: this,
            modal: false,
            noParent: true,
            title: false,
            overrideStart: true
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
            this.uploadFolder = new isic.models.FolderModel({
                name: 'isic_upload_' + Date.now(),
                parentType: 'user',
                parentId: girder.currentUser.id,
                description: 'ISIC uploads'
            });

            this.uploadFolder.once('g:saved', function () {
                this.startUpload(this.uploadFolder);
            }, this).once('g:error', function () {
                girder.events.trigger('g:alert', {
                    icon: 'cancel',
                    text: 'Could not create upload folder.',
                    type: 'error',
                    timeout: 4000
                });
            }, this).save();
        }
    },

    uploadFinished: function (files) {
        this.uploadedCsvFiles = _.pluck(files.files, 'name');
        this.updateUploadWidget();
    },

    startUpload: function (folder) {
        // Configure upload widget and begin upload
        this.uploadWidget.parentType = 'folder';
        this.uploadWidget.parent = folder;
        this.uploadWidget.uploadNextFile();
    },

    updateUploadWidget: function () {
        var visible = false;
        var uploadList = [];
        if (this.uploadedCsvFiles.length) {
            visible = false;
            uploadList = this.uploadedCsvFiles;
        } else {
            visible = true;
        }

        this.$('.isic-upload-widget-container').toggle(visible);
        this.$('.isic-upload-reset-container').toggle(!visible);

        this.uploadWidget.render();
        this.$('.isic-upload-list').text(
            'Uploaded: ' + uploadList.join(', '));
    },

    resetUpload: function () {
        // Delete uploaded files
        this.uploadFolder.once('g:success', function () {
            this.uploadedCsvFiles = [];
            this.updateUploadWidget();
        }, this).removeContents();
    },

    registerMetadata: function (metadataFileId) {
        this.dataset.registerMetadata(metadataFileId);
    }
});

isic.router.route('uploadDatasetMetadata', 'uploadDatasetMetadata', function () {
    if (girder.currentUser) {
        // Registered users must:
        //  (1) Accept the TOS
        //  (2) Request and receive create dataset access
        // before being able to see the upload dataset metadata view
        var nextView = isic.views.UploadDatasetMetadataView;
        if (!isic.models.UserModel.currentUserCanAcceptTerms()) {
            nextView = isic.views.TermsAcceptanceView;
        } else if (!girder.currentUser.canCreateDataset()) {
            nextView = isic.views.UploadDatasetRequestView;
        }
        girder.events.trigger('g:navigateTo', nextView);
    } else {
        // Anonymous users should not be here, so route to home page
        isic.router.navigate('', {trigger: true});
    }
});
