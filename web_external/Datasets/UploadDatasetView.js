isic.views.UploadDatasetView = isic.View.extend({
    events: {
        'click #isic-upload-reset': function (event) {
            this.resetUpload();
        },
        'click #isic-upload-show-license-info-link': 'showLicenseInfo',
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

            // If no files have been uploaded, delegate error handling to submitDataset()
            if (!this.uploadFolder) {
                this.submitDataset(null);
                return;
            }

            // Get file ID of uploaded file, then submit dataset
            var items = new girder.collections.ItemCollection();
            items.once('g:changed', function () {
                if (!items.isEmpty()) {
                    var item = items.first();
                    item.once('g:files', function (fileCollection) {
                        var fileId = fileCollection.first().id;
                        this.submitDataset(fileId);
                    }, this).getFiles();
                } else {
                    this.submitDataset(null);
                }
            }, this).fetch({
                folderId: this.uploadFolder.id
            });
        }
    },

    initialize: function (settings) {
        this.uploadedZipFiles = [];
        this.uploadFolder = null;

        this.termsOfUseWidget = new isic.views.TermsOfUseWidget({
            parentView: this
        });

        this.dataset = new isic.models.DatasetModel();

        this.listenTo(this.dataset, 'isic:ingestImages:success', function () {
            isic.showAlertDialog({
                text: '<h4>Dataset successfully submitted.</h4>',
                escapedHtml: true,
                callback: _.bind(function () {
                    // Navigate to register metadata view
                    isic.router.navigate(
                        'dataset/' + this.dataset.id + '/metadata/register',
                        {trigger: true});
                }, this)
            });
        });

        this.listenTo(this.dataset, 'isic:ingestImages:error', function (resp) {
            isic.showAlertDialog({
                text: '<h4>Error submitting dataset</h4><br>' + _.escape(resp.responseJSON.message),
                escapedHtml: true
            });
            this.$('#isic-dataset-submit').prop('disabled', false);
        });

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

        this.termsOfUseWidget.setElement(
            this.$('#isic-terms-of-use-container')).render();

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
                name: 'isic_dataset_' + Date.now(),
                parentType: 'user',
                parentId: girder.currentUser.id,
                description: 'ISIC dataset upload'
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
        this.uploadedZipFiles = _.pluck(files.files, 'name');
        this.updateUploadWidget();
    },

    startUpload: function (folder) {
        // Configure upload widget and begin upload
        this.uploadWidget.parentType = 'folder';
        this.uploadWidget.parent = folder;
        this.uploadWidget.uploadNextFile();
    },

    /**
     * Submit dataset. Delegate all validation to the server.
     * @param [zipFileId] The ID of the .zip file, or null.
     */
    submitDataset: function (zipFileId) {
        var name = this.$('#isic-dataset-name').val();
        var owner = this.$('#isic-dataset-owner').val();
        var description = this.$('#isic-dataset-description').val();
        var license = this.$('#isic-dataset-license').val();
        var signature = this.$('#isic-dataset-agreement-signature').val();
        var anonymous = this.$('#isic-dataset-attribution-anonymous').prop('checked');
        var attribution = this.$('#isic-dataset-attribution-name').val();

        this.dataset.ingestImages(zipFileId, name, owner, description, license,
            signature, anonymous, attribution);
    },

    updateUploadWidget: function () {
        var visible = false;
        var uploadList = [];
        if (this.uploadedZipFiles.length) {
            visible = false;
            uploadList = this.uploadedZipFiles;
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
            this.uploadedZipFiles = [];
            this.updateUploadWidget();
        }, this).removeContents();
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

isic.views.UploadDatasetRequestView = isic.View.extend({
    events: {
        'submit #isic-dataset-form': function (event) {
            event.preventDefault();
            this.$('#isic-dataset-submit').prop('disabled', true);

            girder.currentUser.setCanCreateDataset(
                // Success callback
                function (resp) {
                    // Refresh page
                    Backbone.history.loadUrl();
                },
                // Failure (or request pending) callback
                function (resp) {
                    // Display notification and route to index
                    isic.showAlertDialog({
                        text: resp.message,
                        callback: function () {
                            isic.router.navigate('', {trigger: true});
                        }
                    });
                }
            );
        }
    },

    initialize: function (settings) {
        this.render();
    },

    render: function () {
        this.$el.html(isic.templates.uploadDatasetRequest({
            user: girder.currentUser
        }));

        return this;
    }
});

isic.router.route('dataset/upload', 'uploadDataset', function () {
    if (girder.currentUser) {
        // Registered users must:
        //  (1) Accept the TOS
        //  (2) Request and receive create dataset access
        // before being able to see the upload dataset view
        var nextView = isic.views.UploadDatasetView;
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
