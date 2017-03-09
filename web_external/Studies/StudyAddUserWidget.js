isic.views.StudyAddUserWidget = isic.View.extend({
    events: {
        'click .isic-add-user-ok-button': function (event) {
            if (!this.user) {
                return;
            }

            var study = new isic.models.StudyModel({
                _id: this.study.id
            }).once('g:addedUser', function () {
                this.trigger('g:saved');
                $('.modal').modal('hide');
            }, this).once('g:error', function () {
                $('.modal').modal('hide');
            });
            study.addUser(this.user.id);
        }
    },

    /**
     * @param {isic.models.StudyModel} settings.study
     */
    initialize: function (settings) {
        this.study = settings.study;
        this.user = null;

        this.searchWidget = new girder.views.SearchFieldWidget({
            placeholder: 'Start typing a name...',
            modes: ['prefix', 'text'],
            types: ['user'],
            parentView: this
        }).on('g:resultClicked', this._addUser, this);
    },

    render: function () {
        var modal = this.$el.html(isic.templates.studyAddUserWidget({
            study: this.study
        })).girderModal(this).on('shown.bs.modal', function () {
        }).on('hidden.bs.modal', function () {
            girder.dialogs.handleClose('addUser');
        }).on('ready.girder.modal', function () {
        });

        modal.trigger($.Event('ready.girder.modal', {
            relatedTarget: modal
        }));

        this.searchWidget.setElement(this.$('.isic-search-field-container')).render();

        // Disable OK button
        this.$('.isic-add-user-ok-button').prop('disabled', true);

        girder.dialogs.handleOpen('addUser');

        return this;
    },

    _addUser: function (user) {
        this.searchWidget.resetState();

        // Check whether user is already in study
        var userIds = _.pluck(this.study.get('users'), '_id');
        if (_.contains(userIds, user.id)) {
            this.$('.isic-user-container').html('(user is already in study)');
            return;
        }

        this.user = user;

        this.$('.isic-user-container').html(isic.templates.userInfo({
            user: this.user
        }));

        // Enable OK button
        this.$('.isic-add-user-ok-button').prop('disabled', false);
    }
});
