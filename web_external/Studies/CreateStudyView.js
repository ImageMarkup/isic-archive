import $ from 'jquery';
import _ from 'underscore';

import SearchFieldWidget from 'girder/views/widgets/SearchFieldWidget';
import {restRequest} from 'girder/rest';

import FeaturesetModel from '../models/FeaturesetModel';
import View from '../view';
import {showAlertDialog} from '../common/utilities';
import router from '../router';

import CreateStudyPageTemplate from './createStudyPage.pug';
import './createStudyPage.styl';
import FeaturesetListEntryTemplate from './featuresetListEntry.pug';
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
            target.tooltip('hide');

            let listEntry = target.closest('.isic-list-entry');
            let userId = listEntry.data('userId');
            listEntry.remove();

            this._removeUser(userId);
        },

        'click a.isic-featureset-list-entry-action-remove': function (event) {
            let target = $(event.currentTarget);
            target.tooltip('hide');

            let listEntry = target.closest('.isic-list-entry');
            listEntry.remove();

            this._removeFeatureset();
        }
    },

    initialize: function (settings) {
        this.userIds = [];
        this.featuresetId = null;

        this.userSearchWidget = new SearchFieldWidget({
            placeholder: 'Search users...',
            modes: ['prefix', 'text'],
            types: ['user'],
            parentView: this
        }).on('g:resultClicked', this._addUser, this);

        this.featuresetSearchWidget = new SearchFieldWidget({
            placeholder: 'Search featuresets...',
            modes: ['prefix', 'text'],
            types: ['featureset.isic_archive'],
            getInfoCallback: function (type, obj) {
                if (type === 'featureset.isic_archive') {
                    let featureset = new FeaturesetModel(obj);
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
        this.$el.html(CreateStudyPageTemplate());

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

        let userList = this.$('#isic-study-user-list');
        userList.append(UserListEntryTemplate({
            user: user
        }));

        this._makeTooltips();

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

    _addFeatureset: function (featureset) {
        this.featuresetSearchWidget.resetState();

        // Remove existing entries
        this.$('.isic-featureset-list-entry').remove();

        // Add new entry
        // TODO show or link to featureset details
        this.$('#isic-study-featureset-list').append(FeaturesetListEntryTemplate({
            featureset: featureset
        }));

        this._makeTooltips();

        this.featuresetId = featureset.id;
    },

    _removeFeatureset: function () {
        this.featuresetId = null;
    },

    submitStudy: function () {
        let name = $('#isic-study-name').val();
        let featuresetId = this.featuresetId;
        let userIds = JSON.stringify(this.userIds);
        let imageIds = JSON.stringify([]);

        // TODO: move this into the StudyModel
        restRequest({
            type: 'POST',
            path: 'study',
            data: {
                name: name,
                featuresetId: featuresetId,
                userIds: userIds,
                imageIds: imageIds
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
