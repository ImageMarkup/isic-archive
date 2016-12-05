isic.models.MetadataErrorModel = Backbone.Model.extend({
    message: function () {
        return this.get('message');
    }
});

isic.collections.MetadataErrorCollection = Backbone.Collection.extend({
    model: isic.models.MetadataErrorModel
});

isic.models.MetadataFileErrorModel = Backbone.Model.extend({
    initialize: function (options) {
        this.parseErrors = new isic.collections.MetadataErrorCollection(options.parseErrors);
        this.validationErrors = new isic.collections.MetadataErrorCollection(options.validationErrors);
    },

    filename: function () {
        return this.get('filename');
    },

    // Check whether model passed validation
    validated: function () {
        return this.parseErrors.isEmpty() && this.validationErrors.isEmpty();
    }
});

isic.collections.MetadataFileErrorCollection = Backbone.Collection.extend({
    model: isic.models.MetadataFileErrorModel,

    // Check whether all models passed validation
    validated: function () {
        return this.all(function (model) {
            return model.validated();
        });
    }
});

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

// View for a metadata validation results
isic.views.UploadDatasetMetadataValidationView = isic.View.extend({
    events: {
        'click #isic-upload-dataset-metadata-save': function () {
            this.trigger('saveMetadata');
        }
    },
    initialize: function (options) {
        this.listenTo(this.collection, 'reset', this.render);
        this.render();
    },

    render: function () {
        this.$el.html(isic.templates.uploadDatasetMetadataValidationPage({
            errors: this.collection
        }));

        // Show save button when there are no validation errors
        if (this.collection.validated()) {
            this.$('.isic-upload-dataset-metadata-save-button-container').removeClass('hidden');
        }

        return this;
    }
});

isic.views.UploadDatasetMetadataView = isic.View.extend({
    events: {
        'click #isic-upload-reset': function (event) {
            this.resetUpload();
            this.clearResults();
        },
        'click #isic-upload-dataset-metadata-validate': function () {
            var save = false;
            this.validateMetadata(save);
        }
    },

    initialize: function (settings) {
        this.uploadedCsvFiles = [];
        this.uploadFolder = null;

        this.dataset = new isic.models.DatasetModel();
        this.datasets = new isic.collections.DatasetCollection();

        this.metadataFileErrors = new isic.collections.MetadataFileErrorCollection();

        this.selectDatasetView = new isic.views.UploadDatasetMetadataSelectDatasetView({
            collection: this.datasets,
            parentView: this
        });

        this.validationView = new isic.views.UploadDatasetMetadataValidationView({
            collection: this.metadataFileErrors,
            parentView: this
        });

        this.datasets.fetch();

        this.listenTo(this.selectDatasetView, 'changed', this.datasetChanged);
        this.listenTo(this.validationView, 'saveMetadata', function () {
            // Show confirmation dialog
            girder.confirm({
                text: '<h4>Save metadata?</h4>',
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
        });

        this.render();
    },

    datasetChanged: function (datasetId) {
        this.dataset.set({'_id': datasetId});
        this.clearResults();
    },

    render: function () {
        this.$el.html(isic.templates.uploadDatasetMetadata({
            user: girder.currentUser
        }));

        this.selectDatasetView.setElement(
            this.$('#isic-upload-dataset-metadata-dataset-select-container')).render();

        this.validationView.setElement(
            this.$('#isic-upload-dataset-metadata-validation-container')).render();

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
            this.uploadFolder = new girder.models.FolderModel({
                name: 'isic_upload_' + Date.now(),
                parentType: 'user',
                parentId: girder.currentUser.get('_id'),
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
        var uploadList = this.uploadedCsvFiles;

        // Delete uploaded files
        _.each(uploadList, function (name) {
            var items = new girder.collections.ItemCollection();
            items.once('g:changed', function () {
                if (!items.isEmpty()) {
                    var item = items.first();
                    item.destroy();

                    while (uploadList.length) {
                        uploadList.pop();
                    }
                    this.updateUploadWidget();
                }
            }, this).fetch({
                name: name,
                folderId: this.uploadFolder.id
            });
        }, this);
    },

    validateMetadata: function (save) {
        // Require dataset to be selected and CSV file to be uploaded
        var errorMessage = null;
        if (!this.dataset.id) {
            errorMessage = 'Please select a dataset.';
        } else if (_.isEmpty(this.uploadedCsvFiles)) {
            errorMessage = 'Please upload a CSV file.';
        }

        if (errorMessage !== null) {
            isic.showAlertDialog({ text: errorMessage });
            return;
        }

        this.dataset.off().on('isic:validated', function (resp) {
            // Populate metadata file error collection
            this.metadataFileErrors.reset(resp);

            if (save) {
                isic.showAlertDialog({
                    text: '<h4>Metadata successfully saved.</h4>',
                    escapedHtml: true,
                    callback: function () {
                        isic.router.navigate('', {trigger: true});
                    }
                });
            }
        }, this).on('g:error', function (err) {
            isic.showAlertDialog({ text: 'Error: ' + err.responseJSON.message });
        }, this).validateMetadata(this.uploadFolder.id, save);
    },

    clearResults: function () {
        this.metadataFileErrors.reset();
    }
});

isic.router.route('uploadDatasetMetadata', 'uploadDatasetMetadata', function () {
    // Route registered users to upload dataset metadata view or upload dataset request view.
    // Route anonymous users to index.
    if (girder.currentUser) {
        var view;
        if (girder.currentUser.canCreateDataset()) {
            view = isic.views.UploadDatasetMetadataView;
        } else {
            view = isic.views.UploadDatasetRequestView;
        }
        girder.events.trigger('g:navigateTo', view);
    } else {
        isic.router.navigate('', {trigger: true});
    }
});
