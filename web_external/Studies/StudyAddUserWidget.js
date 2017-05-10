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

var StudyAddUserWidget = View.extend({
    events: {
        'click .isic-add-user-ok-button': function (event) {
            if (!this.user) {
                return;
            }

            var study = new StudyModel({
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
     * @param {StudyModel} settings.study
     */
    initialize: function (settings) {
        this.study = settings.study;
        this.user = null;

        this.searchWidget = new SearchFieldWidget({
            placeholder: 'Start typing a name...',
            modes: ['prefix', 'text'],
            types: ['user'],
            parentView: this
        }).on('g:resultClicked', this._addUser, this);
    },

    render: function () {
        var modal = this.$el.html(StudyAddUserWidgetTemplate({
            study: this.study
        })).girderModal(this).on('shown.bs.modal', function () {
        }).on('hidden.bs.modal', function () {
            handleClose('addUser');
        }).on('ready.girder.modal', function () {
        });

        modal.trigger($.Event('ready.girder.modal', {
            relatedTarget: modal
        }));

        this.searchWidget.setElement(this.$('.isic-search-field-container')).render();

        // Disable OK button
        this.$('.isic-add-user-ok-button').prop('disabled', true);

        handleOpen('addUser');

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

        this.$('.isic-user-container').html(UserInfoTemplate({
            user: this.user
        }));

        // Enable OK button
        this.$('.isic-add-user-ok-button').prop('disabled', false);
    }
});

export default StudyAddUserWidget;
