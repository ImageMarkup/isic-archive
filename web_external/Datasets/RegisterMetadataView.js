import _ from 'underscore';

import View from '../view';
import {showAlertDialog} from '../common/utilities';
import router from '../router';

import RegisterMetadataTemplate from './registerMetadata.pug';
import './registerMetadata.styl';
import './datasetInfoWidget.styl';

const RegisterMetadataView = View.extend({
    events: {
        'change .isic-register-metadata-file-input': function (event) {
            const file = this._getSelectedFile();
            if (file) {
                this.$('.isic-register-metadata-csv-file').text(file.name);
            }
        },
        'submit #isic-register-metadata-form': function (event) {
            event.preventDefault();
            const file = this._getSelectedFile();
            if (!file) {
                showAlertDialog({ text: 'Please selected a CSV file.' });
                return;
            }

            this.$('#isic-register-metadata-submit').girderEnable(false);
            this._registerMetadata(file);
        }
    },

    /**
     * @param {DatasetModel} settings.dataset
     */
    initialize: function (settings) {
        this.dataset = settings.dataset;

        this.render();
    },

    render: function () {
        this.$el.html(RegisterMetadataTemplate({
            dataset: this.dataset
        }));

        return this;
    },

    /**
     * Get the currently selected File object from file input, or null.
     */
    _getSelectedFile: function () {
        const input = this.$('.isic-register-metadata-file-input').get(0);
        const files = input.files;
        return (files.length ? files[0] : null);
    },

    /**
     * Register a metadata file with the current dataset.
     * @param {File} file - The metadata File object.
     */
    _registerMetadata: function (file) {
        this.dataset.registerMetadata(file.name, file)
            .done(() => {
                showAlertDialog({
                    text: '<h4>Metadata successfully registered.</h4><br>' +
                        'An administrator may contact you via email.',
                    escapedHtml: true,
                    callback: () => {
                        router.navigate('', {trigger: true});
                    }
                });
            })
            .fail((resp) => {
                showAlertDialog({
                    text: `<h4>Error registering metadata</h4><br>${_.escape(resp.responseJSON.message)}`,
                    escapedHtml: true
                });
                this.$('#isic-register-metadata-submit').girderEnable(true);
            });
    }
});

export default RegisterMetadataView;
