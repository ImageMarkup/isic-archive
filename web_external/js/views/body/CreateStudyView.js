isic.views.CreateStudyView = isic.View.extend({
    events: {
        'submit #isic-study-form': function (event) {
            event.preventDefault();
            this.$('#isic-study-submit').prop('disabled', true);
            this.submitStudy();
        },

        'click a.isic-user-list-entry-action-remove': function (event) {
            var target = $(event.currentTarget);
            var listEntry = target.closest('.isic-user-list-entry');
            var userId = listEntry.data('userid');

            // TODO explicitly remove tooltips?

            listEntry.remove();

            this._removeUser(userId);
        }
    },

    initialize: function (settings) {
        this.userIds = [];

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
                    return {
                        text: obj.name,
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

        this.userSearchWidget.setElement(
            this.$('.isic-study-user-search-field-container')).render();
        // this.featuresetSearchWidget.setElement(
        //     this.$('.isic-study-featureset-search-field-container')).render();

        this.$('input#isic-study-name').focus();

        return this;
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

        // TODO tooltips

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
        // TODO
    },

    submitStudy: function () {
        var name = $('#isic-study-name').val();
        var featuresetId = null;
        var userIds = this.userIds;
        var segmentationIds = null;

        // TODO
        girder.restRequest({
            type: 'POST',
            path: 'study',
            data: {
                name: name,
                featuresetId: featuresetId,
                userIds: userIds,
                segmentationIds: segmentationIds
            },
            error: null
        }).done(_.bind(function () {
            girder.confirm({
                text: '<h4>Study created.</h4>',
                yesClass: 'hidden',
                noText: 'OK',
                escapedHtml: true
            });
            isic.router.navigate('', {trigger: true});
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

isic.router.route('createStudy', 'createStudy', function (id) {
    // TODO check whether user can create studies
    girder.events.trigger('g:navigateTo', isic.views.CreateStudyView);
});
