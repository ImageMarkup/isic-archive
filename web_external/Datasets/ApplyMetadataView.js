// Model for a metadata file
isic.models.MetadataFileModel = girder.Model.extend({
    name: function () {
        var time = girder.formatDate(this.get('time'), girder.DATE_SECOND);
        var fileName = this.get('file').name();
        var userName = this.get('user').name();
        return time + ' \u2014 ' + fileName + ' \u2014 ' + userName;
    }
});

// Collection of metadata files as returned by of DatasetModel.getRegisteredMetadata()
isic.collections.MetadataFileCollection = girder.Collection.extend({
    model: isic.models.MetadataFileModel,

    // Sort in reverse chronological order
    sortField: 'time',
    sortDir: girder.SORT_DESC,

    parse: function (data) {
        _.each(data, function (item) {
            item.file = new girder.models.FileModel(item.file);
            item.user = new isic.models.UserModel(item.user);

            // Use file ID as item ID
            item._id = item.file.id;
        });
        return data;
    }
});

// Model for a single metadata error
isic.models.MetadataErrorModel = Backbone.Model.extend({
    description: function () {
        return this.get('description');
    }
});

// Collection of metadata errors. The list of items in the collection is
// meaningful only when initialized() is true.
isic.collections.MetadataErrorCollection = Backbone.Collection.extend({
    model: isic.models.MetadataErrorModel,

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
isic.views.ApplyMetadataSelectFileView = isic.View.extend({
    events: {
        'change': 'fileChanged'
    },

    /**
     * @param {isic.collections.MetadataFileCollection} settings.collection
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

        this.$el.html(isic.templates.applyMetadataSelectFilePage({
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
isic.views.ApplyMetadataView = isic.View.extend({
    events: {
        'click #isic-apply-metadata-download-button': function () {
            // Download selected metadata file
            var fileModel = new girder.models.FileModel({_id: this.file.id});
            fileModel.download();
        },

        'click #isic-apply-metadata-validate-button': function () {
            var save = false;
            this.validateMetadata(save);
        },

        'click #isic-apply-metadata-save': function () {
            // Show confirmation dialog
            girder.confirm({
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
     * @param {isic.models.DatasetModel} settings.dataset
     */
    initialize: function (settings) {
        this.dataset = settings.dataset;

        // Registered metadata files
        this.files = new isic.collections.MetadataFileCollection();

        // Selected metadata file
        this.file = null;

        // Errors in the selected metadata file
        this.errors = new isic.collections.MetadataErrorCollection();

        this.selectFileView = new isic.views.ApplyMetadataSelectFileView({
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
        this.$el.html(isic.templates.applyMetadataPage({
            dataset: this.dataset
        }));

        this.selectFileView.setElement(
            this.$('#isic-apply-metadata-select-file-container')).render();

        this.renderValidationContainer();

        return this;
    },

    renderValidationContainer: function () {
        this.$('#isic-apply-metadata-validation-container').html(
            isic.templates.applyMetadataValidationPage({
                errors: this.errors,
                file: this.file
            }));

        return this;
    },

    validateMetadata: function (save) {
        this.dataset.applyMetadata(this.file.id, save).then(_.bind(function (resp) {
            this.errors.reset(resp, {parse: true});

            if (save) {
                isic.showAlertDialog({
                    text: '<h4>Metadata saved.</h4>',
                    escapedHtml: true,
                    callback: function () {
                        isic.router.navigate('', {trigger: true});
                    }
                });
            }
        }, this), function (err) {
            isic.showAlertDialog({text: 'Error: ' + err.responseJSON.message});
        });
    }
});

isic.router.route('dataset/:id/metadata/apply', 'applyMetadata', function (id) {
    if (girder.currentUser) {
        // Registered users must:
        //  (1) Accept the TOS
        //  (2) Request and receive create dataset access
        // before being able to see the apply metadata view
        if (!isic.models.UserModel.currentUserCanAcceptTerms()) {
            girder.events.trigger('g:navigateTo', isic.views.TermsAcceptanceView);
        } else if (!girder.currentUser.canCreateDataset()) {
            girder.events.trigger('g:navigateTo', isic.views.CreateDatasetRequestView);
        } else {
            // Fetch the dataset, then navigate to the view
            var dataset = new isic.models.DatasetModel({
                _id: id
            }).once('g:fetched', function () {
                girder.events.trigger('g:navigateTo', isic.views.ApplyMetadataView, {
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
