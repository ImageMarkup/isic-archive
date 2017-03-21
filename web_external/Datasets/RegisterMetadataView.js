isic.views.RegisterMetadataView = isic.View.extend({
    events: {
        'click #isic-upload-reset': function (event) {
            this.resetUpload();
        },
        'click #isic-register-metadata-submit': function (event) {
            // Require CSV file to be uploaded
            if (_.isEmpty(this.uploadedCsvFiles) || !this.uploadFolder) {
                isic.showAlertDialog({ text: 'Please upload a CSV file.' });
                return;
            }

            this.$('#isic-register-metadata-submit').prop('disabled', true);

            // Get file ID of uploaded file, then register metadata
            var items = new girder.collections.ItemCollection();
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

    /**
     * @param {isic.models.DatasetModel} settings.dataset
     */
    initialize: function (settings) {
        this.dataset = settings.dataset;

        this.uploadedCsvFiles = [];
        this.uploadFolder = null;

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
                text: '<h4>Error registering metadata</h4><br>' + _.escape(resp.responseJSON.message),
                escapedHtml: true
            });
            this.$('#isic-register-metadata-submit').prop('disabled', false);
        });

        this.render();
    },

    render: function () {
        this.$el.html(isic.templates.registerMetadata({
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
                name: 'isic_metadata_' + Date.now(),
                parentType: 'user',
                parentId: girder.currentUser.id,
                description: 'ISIC metadata upload'
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

isic.router.route('dataset/:id/metadata/register', 'registerMetadata', function (id) {
    if (girder.currentUser) {
        // Registered users must:
        //  (1) Accept the TOS
        //  (2) Request and receive create dataset access
        // before being able to see the register metadata view
        if (!isic.models.UserModel.currentUserCanAcceptTerms()) {
            girder.events.trigger('g:navigateTo', isic.views.TermsAcceptanceView);
        } else if (!girder.currentUser.canCreateDataset()) {
            girder.events.trigger('g:navigateTo', isic.views.UploadDatasetRequestView);
        } else {
            // Fetch the dataset, then navigate to the view
            var dataset = new isic.models.DatasetModel({
                _id: id
            }).once('g:fetched', function () {
                girder.events.trigger('g:navigateTo', isic.views.RegisterMetadataView, {
                    dataset: dataset
                });
            }, this).once('g:error', function () {
                isic.router.navigate('', {trigger: true});
            }, this).fetch();
        }
    } else {
        // Anonymous users should not be here, so route to home page
        isic.router.navigate('', {trigger: true});
    }
});
