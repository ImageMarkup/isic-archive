import $ from 'jquery';
import _ from 'underscore';

import LoadingAnimation from '@girder/core/views/widgets/LoadingAnimation';
import {confirm} from '@girder/core/dialog';

import StudyAddUserWidget from './StudyAddUserWidget';
import View from '../view';
import {showAlertDialog} from '../common/utilities';

import StudyPageTemplate from './studyPage.pug';
import './studyPage.styl';
import '../common/Listing/listingItemPage.styl';

const StudyView = View.extend({
    events: {
        'click .isic-study-add-user-button': function () {
            if (!this.studyAddUserWidget) {
                this.studyAddUserWidget = new StudyAddUserWidget({
                    el: $('#g-dialog-container'),
                    study: this.model,
                    parentView: this
                })
                    .on('g:saved', () => {
                        this.model
                            .once('g:fetched', () => {
                                this.render();
                            })
                            .fetch();
                    });
            }
            this.studyAddUserWidget.render();
        },

        'click .isic-study-remove-user-button': function (event) {
            let target = $(event.currentTarget);
            let userId = target.closest('[data-user-id]').data('userId');
            // TODO: StudyModel.users() should be cached instead of re-created
            let user = this.model.users().get(userId);
            this.confirmRemoveUser(user);
        },

        'click .isic-study-accept-request-button': function (event) {
            let target = $(event.currentTarget);
            let userId = target.closest('[data-user-id]').data('userId');
            let user = this.model.participationRequests().get(userId);
            this.confirmAcceptParticipationRequest(user);
        },

        'click .isic-study-delete-request-button': function (event) {
            let target = $(event.currentTarget);
            let userId = target.closest('[data-user-id]').data('userId');
            let user = this.model.participationRequests().get(userId);
            this.confirmDeleteParticipationRequest(user);
        },

        'click .isic-study-destroy-button': 'confirmDestroy'
    },

    /**
     * @param {StudyModel} settings.model
     */
    initialize: function (settings) {
        // Display loading indicator
        this.loadingAnimation = new LoadingAnimation({
            el: this.el,
            parentView: this
        }).render();

        this.model
            .once('g:fetched', () => {
                // Don't "this.loadingAnimation.destroy()", as it will unbind all events on "this.el"
                delete this.loadingAnimation;

                this.render();
            })
            .fetch();
    },

    render: function () {
        this.$el.html(StudyPageTemplate({
            study: this.model,
            formatDate: this.formatDate
        }));

        return this;
    },

    confirmRemoveUser: function (user) {
        confirm({
            text: `<h4>Permanently remove <b>"${_.escape(user.name())}"</b> from study?</h4>`,
            escapedHtml: true,
            confirmCallback: () => {
                // Ensure dialog is hidden before continuing. Otherwise,
                // when destroy() displays its modal alert dialog,
                // the Bootstrap-created element with class "modal-backdrop"
                // is erroneously not removed.
                $('#g-dialog-container').on('hidden.bs.modal', _.bind(this.removeUser, this, user));
            }
        });
    },

    removeUser: function (user) {
        this.model
            .removeUser(user)
            .done(() => {
                this.model
                    .once('g:fetched', () => {
                        // TODO: re-render this via model events instead
                        this.render();
                    })
                    .fetch();
                showAlertDialog({
                    text: `<h4>Annotator <b>"${_.escape(user.name())}"</b> deleted</h4>'`,
                    escapedHtml: true
                });
            })
            .fail((resp) => {
                showAlertDialog({
                    text: `<h4>Error deleting annotator</h4><br>${_.escape(resp.responseJSON.message)}`,
                    escapedHtml: true
                });
            });
    },

    confirmAcceptParticipationRequest: function (user) {
        confirm({
            text: `<h4>Add user <b>"${_.escape(user.name())}"</b> to the study?</h4>`,
            escapedHtml: true,
            confirmCallback: () => {
                // Ensure dialog is hidden before continuing. Otherwise,
                // when destroy() displays its modal alert dialog,
                // the Bootstrap-created element with class "modal-backdrop"
                // is erroneously not removed.
                $('#g-dialog-container').on('hidden.bs.modal', _.bind(this.acceptParticipationRequest, this, user));
            }
        });
    },

    acceptParticipationRequest: function (user) {
        this.model
            .addUser(user)
            .done(() => {
                this.model
                    .once('g:fetched', () => {
                        this.render();
                    })
                    .fetch();
            })
            .fail((resp) => {
                showAlertDialog({
                    text: `<h4>Error adding user to the study</h4><br>${_.escape(resp.responseJSON.message)}`,
                    escapedHtml: true
                });
            });
    },

    confirmDeleteParticipationRequest: function (user) {
        confirm({
            text: `<h4>Delete participation request from <b>"${_.escape(user.name())}"</b>?</h4>`,
            escapedHtml: true,
            confirmCallback: () => {
                // Ensure dialog is hidden before continuing. Otherwise,
                // when destroy() displays its modal alert dialog,
                // the Bootstrap-created element with class "modal-backdrop"
                // is erroneously not removed.
                $('#g-dialog-container').on('hidden.bs.modal', _.bind(this.deleteParticipationRequest, this, user));
            }
        });
    },

    deleteParticipationRequest: function (user) {
        this.model
            .deleteParticipationRequest(user)
            .done(() => {
                this.model
                    .once('g:fetched', () => {
                        this.render();
                    })
                    .fetch();
            })
            .fail((resp) => {
                showAlertDialog({
                    text: `<h4>Error deleting participation request</h4><br>${_.escape(resp.responseJSON.message)}`,
                    escapedHtml: true
                });
            });
    },

    confirmDestroy: function () {
        confirm({
            text: `<h4>Permanently delete <b>"${_.escape(this.model.name())}"</b> study?</h4>`,
            escapedHtml: true,
            confirmCallback: () => {
                // Ensure dialog is hidden before continuing. Otherwise,
                // when destroy() displays its modal alert dialog,
                // the Bootstrap-created element with class "modal-backdrop"
                // is erroneously not removed.
                $('#g-dialog-container').on('hidden.bs.modal', _.bind(this.destroyModel, this));
            }
        });
    },

    destroyModel: function () {
        this.model.destroy({
            success: function (model, resp, options) {
                showAlertDialog({
                    text: `<h4>Study <b>"${_.escape(model.name())}"</b> deleted</h4>`,
                    escapedHtml: true
                });
            },
            error: function (model, resp, options) {
                showAlertDialog({
                    text: `<h4>Error deleting study</h4><br>${_.escape(resp.responseJSON.message)}`,
                    escapedHtml: true
                });
            }
        });
    }
});

export default StudyView;
