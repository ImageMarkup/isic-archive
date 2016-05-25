isic.views.UploadDatasetView = isic.View.extend({
    events: {
        'change input[name="attribution"]': function (event) {
            var target = $(event.target);
            if (target.val() === "anonymous") {
                this.$('#isic-dataset-attribution-name').attr('disabled', true);
            } else {
                this.$('#isic-dataset-attribution-name').attr('disabled', false);
            }
        }
    },

    initialize: function (settings) {
        girder.cancelRestRequests('fetch');

        this.uploadWidget1 = new girder.views.UploadWidget({
            parentView: this,
            modal: false,
            parentType: 'folder',
            title: false,
            parent: null
        }).on('g:uploadFinished', this._upload1Finished, this);

        this.uploadWidget2 = new girder.views.UploadWidget({
            parentView: this,
            modal: false,
            parentType: 'folder',
            title: false,
            parent: null
        }).on('g:uploadFinished', this._upload2Finished, this);

        this.render();
    },

    render: function () {
        this.$el.html(isic.templates.uploadDataset({
            user: girder.currentUser
        }));

        this.uploadWidget1.setElement(this.$('.isic-upload-images')).render();
        this.uploadWidget2.setElement(this.$('.isic-upload-metadata')).render();

        return this;
    },

    _upload1Finished: function (info) {
        this.uploadWidget1.render();
    },

    _upload2Finished: function (info) {
        this.uploadWidget2.render();
    }
});

isic.router.route('uploadDataset', 'uploadDataset', function (id) {
    girder.events.trigger('g:navigateTo', isic.views.UploadDatasetView);
});
