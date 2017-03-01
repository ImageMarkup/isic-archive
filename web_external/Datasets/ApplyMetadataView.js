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
isic.models.MetadataErrorModel = girder.Model.extend({
    description: function () {
        return this.get('description');
    }
});

// Collection of metadata errors
isic.collections.MetadataErrorCollection = girder.Collection.extend({
    model: isic.models.MetadataErrorModel
});

// Model for the result of DatasetModel.applyMetadata()
isic.models.MetadataFileErrorModel = girder.Model.extend({
    defaults: {
        errors: new isic.collections.MetadataErrorCollection()
    },

    parse: function (data) {
        data.errors = new isic.collections.MetadataErrorCollection(
            _.has(data, 'errors') ? data.errors : null);
        return data;
    },

    empty: function () {
        return !this.has('fileId');
    },

    fileId: function () {
        return this.get('fileId');
    },

    errors: function () {
        return this.get('errors');
    },

    hasErrors: function () {
        return this.has('errors') && !this.get('errors').isEmpty();
    }
});

// View for a collection of metadata files in a select tag
isic.views.ApplyMetadataSelectFileView = isic.View.extend({
    events: {
        'change': 'fileChanged'
    },

    initialize: function (options) {
        this.listenTo(this.collection, 'reset', this.render);
        this.render();
    },

    fileChanged: function () {
        var fileId = this.$('select').val();
        var file = this.collection.get(fileId);
        this.trigger('changed', file);
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

// View for metadata validation results
isic.views.ApplyMetadataValidationView = isic.View.extend({
    events: {
        'click #isic-apply-metadata-save': function () {
            this.trigger('save');
        }
    },

    // Initialize with:
    //   model: MetadataFileErrorModel
    //   file: MetadataFileModel
    initialize: function (options) {
        this.file = options.file;
        this.listenTo(this.model, 'change', this.render);
        this.render();
    },

    render: function () {
        this.$el.html(isic.templates.applyMetadataValidationPage({
            model: this.model,
            file: this.file
        }));

        // Show save button if metadata is valid
        if (!this.model.hasErrors()) {
            this.$('.isic-apply-metadata-save-button-container').removeClass('hidden');
        }

        return this;
    }
});

// View to select a registered metadata file, validate the metadata, and save
// the metadata to the dataset if validation is successful.
isic.views.ApplyMetadataView = isic.View.extend({
    events: {
        'click #isic-apply-metadata-validate-button': function () {
            var save = false;
            this.validateMetadata(save);
        }
    },

    initialize: function (settings) {
        this.dataset = settings.dataset;

        this.file = new isic.models.MetadataFileModel();
        this.files = new isic.collections.MetadataFileCollection();

        this.metadataFileError = new isic.models.MetadataFileErrorModel();

        this.selectFileView = new isic.views.ApplyMetadataSelectFileView({
            collection: this.files,
            parentView: this
        });

        this.validationView = new isic.views.ApplyMetadataValidationView({
            model: this.metadataFileError,
            file: this.file,
            parentView: this
        });

        this.listenTo(this.selectFileView, 'changed', this.fileChanged);

        this.listenTo(this.validationView, 'save', function () {
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
        });

        this.dataset.getRegisteredMetadata().done(_.bind(function (resp) {
            this.files.reset(resp, {parse: true});
        }, this));

        this.render();
    },

    fileChanged: function (file) {
        this.file.set(file.attributes);
        this.clearResults();

        // Enable Validate button
        this.$('#isic-apply-metadata-validate-button').removeAttr('disabled');
    },

    render: function () {
        this.$el.html(isic.templates.applyMetadataPage());

        this.selectFileView.setElement(
            this.$('#isic-apply-metadata-select-file-container')).render();

        this.validationView.setElement(
            this.$('#isic-apply-metadata-validation-container')).render();

        return this;
    },

    validateMetadata: function (save) {
        this.dataset.applyMetadata(this.file.id, save).then(_.bind(function (resp) {
            this.metadataFileError.set(this.metadataFileError.parse(resp));

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
    },

    clearResults: function () {
        this.metadataFileError.clear();
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
            girder.events.trigger('g:navigateTo', isic.views.UploadDatasetRequestView);
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
