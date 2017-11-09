import $ from 'jquery';
import _ from 'underscore';

import SearchFieldWidget from 'girder/views/widgets/SearchFieldWidget';
import {restRequest} from 'girder/rest';

import View from '../view';
import {showAlertDialog} from '../common/utilities';
import router from '../router';

import SelectFeaturesWidget from './selectFeaturesWidget';

import CreateStudyPageTemplate from './createStudyPage.pug';
import './createStudyPage.styl';
import UserListEntryTemplate from './userListEntry.pug';
import '../common/Listing/listingPage.styl';

const CreateStudyView = View.extend({
    events: {
        'submit #isic-study-form': function (event) {
            event.preventDefault();
            this.$('#isic-study-submit').girderEnable(false);
            this.submitStudy();
        },

        'click a.isic-user-list-entry-action-remove': function (event) {
            let target = $(event.currentTarget);

            let listEntry = target.closest('.isic-list-entry');
            let userId = listEntry.data('userId');
            listEntry.remove();

            this._removeUser(userId);
        }
    },

    initialize: function (settings) {
        this.userIds = [];

        this.userSearchWidget = new SearchFieldWidget({
            placeholder: 'Search users...',
            modes: ['prefix', 'text'],
            types: ['user'],
            parentView: this
        }).on('g:resultClicked', this._addUser, this);

        this.selectFeaturesWidget = new SelectFeaturesWidget({
            parentView: this
        });

        this.render();
    },

    render: function () {
        this.$el.html(CreateStudyPageTemplate());

        this.userSearchWidget.setElement(
            this.$('.isic-study-user-search-field-container')).render();

        this.selectFeaturesWidget
            .render()
            .$el.appendTo(this.$('.isic-study-features-container'));

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

        let userList = this.$('#isic-study-user-list');
        userList.append(UserListEntryTemplate({
            user: user
        }));

        userList.animate({
            scrollTop: userList[0].scrollHeight
        }, 1000);
    },

    _removeUser: function (userId) {
        let index = _.indexOf(this.userIds, userId);
        if (index > -1) {
            this.userIds.splice(index);
        }
    },

    submitStudy: function () {
        let name = $('#isic-study-name').val();
        let featureIds = this.selectFeaturesWidget.getSelectedFeatureIds();
        let userIds = this.userIds;
        let imageIds = [];

        // TODO: move this into the StudyModel
        restRequest({
            method: 'POST',
            url: 'study',
            data: {
                name: name,
                featureIds: JSON.stringify(featureIds),
                userIds: JSON.stringify(userIds),
                imageIds: JSON.stringify(imageIds)
            },
            error: null
        }).done(() => {
            showAlertDialog({
                text: `<h4>Study <b>"${_.escape(name)}"</b> created</h4>`,
                escapedHtml: true
            });
            // TODO route directly to study
            router.navigate('studies', {trigger: true});
        }).fail((resp) => {
            showAlertDialog({
                text: `<h4>Error creating study</h4><br>${_.escape(resp.responseJSON.message)}`,
                escapedHtml: true
            });
            this.$('#isic-study-submit').girderEnable(true);
        });
    }
});

export default CreateStudyView;
