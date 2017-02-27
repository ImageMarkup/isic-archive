isic.views.CreateStudyView = isic.View.extend({
    events: {
        'submit #isic-study-form': function (event) {
            event.preventDefault();
            this.$('#isic-study-submit').prop('disabled', true);
            this.submitStudy();
        },

        'click a.isic-user-list-entry-action-remove': function (event) {
            var target = $(event.currentTarget);
            target.tooltip('hide');

            var listEntry = target.closest('.isic-list-entry');
            var userId = listEntry.data('userid');
            listEntry.remove();

            this._removeUser(userId);
        },

        'click a.isic-featureset-list-entry-action-remove': function (event) {
            var target = $(event.currentTarget);
            target.tooltip('hide');

            var listEntry = target.closest('.isic-list-entry');
            listEntry.remove();

            this._removeFeatureset();
        }
    },

    initialize: function (settings) {
        this.userIds = [];
        this.featuresetId = null;

        this.userSearchWidget = new girder.views.SearchFieldWidget({
            placeholder: 'Search users...',
            modes: ['prefix', 'text'],
            types: ['user'],
            parentView: this
        }).on('g:resultClicked', this._addUser, this);

        this.featuresetSearchWidget = new girder.views.SearchFieldWidget({
            placeholder: 'Search featuresets...',
            modes: ['prefix', 'text'],
            types: ['featureset.isic_archive'],
            getInfoCallback: function (type, obj) {
                if (type === 'featureset.isic_archive') {
                    var featureset = new isic.models.FeaturesetModel(obj);
                    return {
                        text: featureset.name(),
                        icon: 'th'
                    };
                }
            },
            parentView: this
        }).on('g:resultClicked', this._addFeatureset, this);

        this.render();
    },

    render: function () {
        this.$el.html(isic.templates.createStudyPage({
        }));

        this._makeTooltips();

        this.userSearchWidget.setElement(
            this.$('.isic-study-user-search-field-container')).render();
        this.featuresetSearchWidget.setElement(
            this.$('.isic-study-featureset-search-field-container')).render();

        this.$('input#isic-study-name').focus();

        return this;
    },

    _makeTooltips: function () {
        this.$('.isic-list-entry-action-remove').tooltip({
            placement: 'bottom',
            animation: false,
            delay: {
                show: 100
            }
        });
    },

    _addUser: function (user) {
        this.userSearchWidget.resetState();

        // Ignore if user is already selected
        if (_.contains(this.userIds, user.id)) {
            return;
        }
        this.userIds.push(user.id);

        var userList = this.$('#isic-study-user-list');
        userList.append(isic.templates.userListEntry({
            user: user
        }));

        this._makeTooltips();

        userList.animate({
            scrollTop: userList[0].scrollHeight
        }, 1000);
    },

    _removeUser: function (userId) {
        var index = _.indexOf(this.userIds, userId);
        if (index > -1) {
            this.userIds.splice(index);
        }
    },

    _addFeatureset: function (featureset) {
        this.featuresetSearchWidget.resetState();

        // Remove existing entries
        this.$('.isic-featureset-list-entry').remove();

        // Add new entry
        // TODO show or link to featureset details
        this.$('#isic-study-featureset-list').append(isic.templates.featuresetListEntry({
            featureset: featureset
        }));

        this._makeTooltips();

        this.featuresetId = featureset.id;
    },

    _removeFeatureset: function () {
        this.featuresetId = null;
    },

    submitStudy: function () {
        var name = $('#isic-study-name').val();
        var featuresetId = this.featuresetId;
        var userIds = JSON.stringify(this.userIds);
        var imageIds = JSON.stringify([]);

        // TODO: move this into the StudyModel
        girder.restRequest({
            type: 'POST',
            path: 'study',
            data: {
                name: name,
                featuresetId: featuresetId,
                userIds: userIds,
                imageIds: imageIds
            },
            error: null
        }).done(_.bind(function () {
            girder.confirm({
                text: '<h4>Study <b>"' + name + '"</b> created</h4>',
                yesClass: 'hidden',
                noText: 'OK',
                escapedHtml: true
            });
            // TODO route directly to study
            isic.router.navigate('studies', {trigger: true});
        }, this)).error(_.bind(function (resp) {
            // TODO: add custom error dialog instead of using confirm dialog
            girder.confirm({
                text: '<h4>Error creating study</h4><br>' + resp.responseJSON.message,
                yesClass: 'hidden',
                noText: 'OK',
                escapedHtml: true
            });
            this.$('#isic-study-submit').prop('disabled', false);
        }, this));
    }
});

isic.router.route('createStudy', 'createStudy', function () {
    // Route to index if user isn't a study administrator
    if (girder.currentUser && girder.currentUser.canAdminStudy()) {
        girder.events.trigger('g:navigateTo', isic.views.CreateStudyView);
    } else {
        isic.router.navigate('', {trigger: true});
    }
});
