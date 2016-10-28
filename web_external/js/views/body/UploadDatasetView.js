isic.views.UploadDatasetView = isic.View.extend({
    events: {
        'click #isic-upload-images': function (event) {
            this.$('#isic-upload-images').addClass('active');
            this.$('#isic-upload-metadata').removeClass('active');
            this.initializeUploadWidget();
            this.updateUploadWidget();
        },
        'click #isic-upload-metadata': function (event) {
            this.$('#isic-upload-images').removeClass('active');
            this.$('#isic-upload-metadata').addClass('active');
            this.initializeUploadWidget();
            this.updateUploadWidget();
        },
        'click #isic-upload-reset': function (event) {
            this.resetUpload();
        },
        'click .isic-dataset-agreement-link': 'showLicenseInfo',
        'change input[name="attribution"]': function (event) {
            // Update attribution name field sensitivity
            var target = $(event.target);
            if (target.val() === 'anonymous') {
                this.$('#isic-dataset-attribution-name').prop('disabled', true);
            } else {
                this.$('#isic-dataset-attribution-name').prop('disabled', false);
            }
        },
        'change #isic-dataset-license': function (event) {
            // Disable anonymous attribution unless CC-0 license is selected
            var target = $(event.target);
            var anonymous = this.$('#isic-dataset-attribution-anonymous');
            if (target.val() === 'CC-0') {
                anonymous.prop('disabled', false);
            } else {
                if (anonymous.prop('checked')) {
                    this.$('#isic-dataset-attribution-attributed-to').prop('checked', true);
                    this.$('#isic-dataset-attribution-attributed-to').change();
                }
                anonymous.prop('disabled', true);
            }
        },
        'submit #isic-dataset-form': function (event) {
            event.preventDefault();
            this.$('#isic-dataset-submit').prop('disabled', true);
            this.submitDataset();
        }
    },

    initialize: function (settings) {
        this.uploadedZipFiles = [];
        this.uploadedCsvFiles = [];
        this.uploadFolder = null;

        this.render();
    },

    render: function () {
        this.$el.html(isic.templates.uploadDataset({
            user: girder.currentUser
        }));

        if (!this.uploadWidget) {
            this.initializeUploadWidget();
        }
        this.updateUploadWidget();

        this.$('input#isic-dataset-name').focus();

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
        var filenames = _.pluck(files.files, 'name');
        if (this.uploadingImages()) {
            this.uploadedZipFiles = filenames;
        } else {
            this.uploadedCsvFiles = filenames;
        }
        this.updateUploadWidget();
    },

    startUpload: function (folder) {
        // Configure upload widget and begin upload
        this.uploadWidget.parentType = 'folder';
        this.uploadWidget.parent = folder;
        this.uploadWidget.uploadNextFile();
    },

    submitDataset: function () {
        var name = $('#isic-dataset-name').val();
        var description = $('#isic-dataset-description').val();
        var license = $('#isic-dataset-license').val();
        var signature = $('#isic-dataset-agreement-signature').val();
        var anonymous = $('#isic-dataset-attribution-anonymous').prop('checked');
        var attribution = $('#isic-dataset-attribution-name').val();
        var uploadFolderId = this.uploadFolder ? this.uploadFolder.id : null;

        // Post dataset
        // TODO: processing happens synchronously; revisit using jobs?
        girder.restRequest({
            type: 'POST',
            path: 'dataset',
            data: {
                uploadFolderId: uploadFolderId,
                name: name,
                description: description,
                license: license,
                signature: signature,
                anonymous: anonymous,
                attribution: attribution
            },
            error: null
        }).done(_.bind(function () {
            // TODO: if updated to use jobs, navigate to job status page instead
            girder.confirm({
                text: '<h4>Dataset successfully submitted.</h4>',
                yesClass: 'hidden',
                noText: 'OK',
                escapedHtml: true
            });
            isic.router.navigate('', {trigger: true});
        }, this)).error(_.bind(function (resp) {
            // TODO: add custom error dialog instead of using confirm dialog
            girder.confirm({
                text: '<h4>Error submitting dataset</h4><br>' + resp.responseJSON.message,
                yesClass: 'hidden',
                noText: 'OK',
                escapedHtml: true
            });
            this.$('#isic-dataset-submit').prop('disabled', false);
        }, this));
    },

    uploadingImages: function () {
        return (this.$('#isic-upload-images.active').length > 0);
    },

    updateUploadWidget: function () {
        var visible = false;
        var uploadList = [];
        var uploadingImages = this.uploadingImages();
        if (uploadingImages) {
            if (this.uploadedZipFiles.length) {
                visible = false;
                uploadList = this.uploadedZipFiles;
            } else {
                visible = true;
            }
        } else {
            if (this.uploadedCsvFiles.length) {
                visible = false;
                uploadList = this.uploadedCsvFiles;
            } else {
                visible = true;
            }
        }

        this.$('.isic-upload-description-container').toggle(visible);
        this.$('.isic-upload-description-zip').toggle(uploadingImages);
        this.$('.isic-upload-description-csv').toggle(!uploadingImages);
        this.$('.isic-upload-widget-container').toggle(visible);
        this.$('.isic-upload-reset-container').toggle(!visible);

        this.uploadWidget.render();
        this.$('.isic-upload-list').text(
            'Uploaded: ' + uploadList.join(', '));
    },

    resetUpload: function () {
        var uploadList = null;
        if (this.uploadingImages()) {
            uploadList = this.uploadedZipFiles;
        } else {
            uploadList = this.uploadedCsvFiles;
        }

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

    showLicenseInfo: function () {
        if (!this.licenseInfoWidget) {
            this.licenseInfoWidget = new isic.views.UploadDatasetLicenseInfoWidget({
                el: $('#g-dialog-container'),
                parentView: this
            });
        }
        this.licenseInfoWidget.render();
    }
});

isic.router.route('uploadDataset', 'uploadDataset', function (id) {
    // Route to index if user doesn't have permission to contribute datasets
    var datasetModel = new isic.models.DatasetModel();
    datasetModel.userCanContribute(girder.currentUser).then(_.bind(function (datasetContributor) {
        if (datasetContributor) {
            girder.events.trigger('g:navigateTo', isic.views.UploadDatasetView);
        } else {
            isic.router.navigate('', {trigger: true});
        }
    }, this));
});
