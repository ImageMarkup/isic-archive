import $ from 'jquery';
import _ from 'underscore';

import LoadingAnimation from 'girder/views/widgets/LoadingAnimation';
import {confirm} from 'girder/dialog';

import View from '../view';
import {showAlertDialog} from '../common/utilities';

import FeaturesetPageTemplate from './featuresetPage.pug';
import './featuresetPage.styl';
import '../common/Listing/listingItemPage.styl';

var FeaturesetView = View.extend({
    events: {
        'click .isic-featureset-destroy-button': 'confirmDestroy'
    },

    /**
     * @param {FeaturesetModel} settings.model
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
        this.$el.html(FeaturesetPageTemplate({
            featureset: this.model,
            formatDate: this.formatDate
        }));

        return this;
    },

    confirmDestroy: function () {
        confirm({
            text: '<h4>Permanently delete <b>"' + _.escape(this.model.name()) + '"</b> featureset?</h4>',
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
                    text: '<h4>Featureset <b>"' + _.escape(model.name()) + '"</b> deleted</h4>',
                    escapedHtml: true
                });
            },
            error: function (model, resp, options) {
                showAlertDialog({
                    text: '<h4>Error deleting featureset</h4><br>' + _.escape(resp.responseJSON.message),
                    escapedHtml: true
                });
            }
        });
    }
});

export default FeaturesetView;
