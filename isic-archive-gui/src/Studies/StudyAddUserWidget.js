import $ from 'jquery';
import _ from 'underscore';

import SearchFieldWidget from 'girder/views/widgets/SearchFieldWidget';
import {handleClose, handleOpen} from 'girder/dialog';

import StudyModel from '../models/StudyModel';
import View from '../view';

import StudyAddUserWidgetTemplate from './studyAddUserWidget.pug';
import './studyAddUserWidget.styl';
import UserInfoTemplate from './userInfo.pug';
import './userInfo.styl';

const StudyAddUserWidget = View.extend({
    events: {
        'click .isic-add-user-ok-button': function (event) {
            if (!this.user) {
                return;
            }

            let study = new StudyModel({
                _id: this.study.id
            });
            study
                .addUser(this.user)
                .done(() => {
                    this.trigger('g:saved');
                    $('.modal').modal('hide');
                })
                .fail((resp) => {
                    $('.modal').modal('hide');
                });
        }
    },

    /**
     * @param {StudyModel} settings.study
     */
    initialize: function (settings) {
        this.study = settings.study;
        this.user = null;

        this.searchWidget = new SearchFieldWidget({
            placeholder: 'Start typing a name...',
            modes: ['prefix', 'text'],
            types: ['user'],
            noResultsPage: true,
            parentView: this
        }).on('g:resultClicked', this._addUser, this);
    },

    render: function () {
        let modal = this.$el.html(StudyAddUserWidgetTemplate({
            study: this.study
        }));
        modal
            .girderModal(this)
            .on('shown.bs.modal', () => {
            })
            .on('hidden.bs.modal', () => {
                handleClose('addUser');
            })
            .on('ready.girder.modal', () => {
            })
            .trigger($.Event('ready.girder.modal', {
                relatedTarget: modal
            }));

        this.searchWidget.setElement(this.$('.isic-search-field-container')).render();

        // Disable OK button
        this.$('.isic-add-user-ok-button').girderEnable(false);

        handleOpen('addUser');

        return this;
    },

    _addUser: function (user) {
        this.searchWidget.resetState();

        // Check whether user is already in study
        let userIds = _.pluck(this.study.get('users'), '_id');
        if (_.contains(userIds, user.id)) {
            this.$('.isic-user-container').html('(user is already in study)');
            return;
        }

        this.user = user;

        this.$('.isic-user-container').html(UserInfoTemplate({
            user: this.user
        }));

        // Enable OK button
        this.$('.isic-add-user-ok-button').girderEnable(true);
    }
});

export default StudyAddUserWidget;
