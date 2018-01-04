import $ from 'jquery';
import _ from 'underscore';

import DatasetModel from '../models/DatasetModel';
import CreateDatasetLicenseInfoWidget from './CreateDatasetLicenseInfoWidget';
import View from '../view';
import {showAlertDialog} from '../common/utilities';
import router from '../router';

import CreateDatasetTemplate from './createDataset.pug';
import './createDataset.styl';

const CreateDatasetView = View.extend({
    events: {
        'click #isic-create-dataset-show-license-info-link': '_showLicenseInfo',

        'change #isic-create-dataset-name': function () {
            this.dataset.set('name', this.$('#isic-create-dataset-name').val());
        },
        'change #isic-create-dataset-description': function () {
            this.dataset.set('description', this.$('#isic-create-dataset-description').val());
        },
        'change #isic-create-dataset-owner': function () {
            this.dataset.set('owner', this.$('#isic-create-dataset-owner').val());
        },
        'change #isic-create-dataset-license': '_setLicense',
        'change input[name="attribution"],#isic-create-dataset-attribution-name': '_setAttribution',

        'submit #isic-create-dataset-form': function (event) {
            event.preventDefault();
            this._submit();
        }
    },

    initialize: function (settings) {
        this.dataset = new DatasetModel();

        this.listenTo(this.dataset, 'change:license', this._onChangeLicense);
        this.listenTo(this.dataset, 'change:attribution', this._onChangeAttribution);

        this.render();

        // Since "this.dataset" is initialized as empty and there's no data binding of initial model
        // values into the template, some fields with default values (as determined by the template)
        // will never be set into the model if the user doesn't change them.
        // TODO: This should be fixed by either having robust two-way data binding, or by reverting
        // to setting model values just before submission.
        this._setLicense();
        this._setAttribution();
    },

    render: function () {
        this.$el.html(CreateDatasetTemplate());

        this.$('input#isic-create-dataset-name').focus();

        return this;
    },

    _setLicense: function () {
        this.dataset.set('license', this.$('#isic-create-dataset-license').val());
    },

    _setAttribution: function () {
        let anonymous = this.$('#isic-create-dataset-attribution-anonymous').prop('checked');
        const attribution = this.$('#isic-create-dataset-attribution-name').val();
        if (_.contains(['anonymous', 'anon'], attribution.toLowerCase())) {
            // This could lead to a non-valid UI state, but it will be caught by server-side
            // validation and it's still easy for the user to resolve
            anonymous = true;
        }
        this.dataset.set('attribution', anonymous ? 'Anonymous' : attribution);
    },

    _showLicenseInfo: function () {
        if (!this.licenseInfoWidget) {
            this.licenseInfoWidget = new CreateDatasetLicenseInfoWidget({
                el: $('#g-dialog-container'),
                parentView: this
            });
        }
        this.licenseInfoWidget.render();
    },

    _onChangeLicense: function () {
        // If a non-CC-0 license is selected, disable anonymous attribution
        const isCC0 = this.dataset.get('license') === 'CC-0';
        const isAnonymous = this.dataset.get('attribution') === 'Anonymous';

        this.$('#isic-create-dataset-attribution-anonymous').girderEnable(isCC0);
        if (!isCC0 && isAnonymous) {
            // This may no longer be anonymous
            this.dataset.set('attribution', '');
        }
    },

    _onChangeAttribution: function () {
        // If anonymous attribution is selected, disable the attribution name box
        const isAnonymous = this.dataset.get('attribution') === 'Anonymous';
        if (isAnonymous) {
            this.$('#isic-create-dataset-attribution-anonymous').prop('checked', true);
            this.$('#isic-create-dataset-attribution-name')
                .girderEnable(false)
                .val('');
        } else {
            this.$('#isic-create-dataset-attribution-attributed-to').prop('checked', true);
            this.$('#isic-create-dataset-attribution-name').girderEnable(true);
        }
    },

    _submit: function () {
        this.$('#isic-create-dataset-submit').girderEnable(false);

        this.dataset
            .save()
            .done(() => {
                showAlertDialog({
                    text: '<h4>Dataset created successfully.</h4>',
                    escapedHtml: true,
                    callback: () => {
                        // Navigate to dataset view
                        router.navigate(
                            'dataset',
                            {trigger: true});
                    }
                });
            })
            .fail((resp) => {
                showAlertDialog({
                    text: `<h4>Error submitting dataset</h4><br>${_.escape(resp.responseJSON.message)}`,
                    escapedHtml: true
                });
                this.$('#isic-create-dataset-submit').girderEnable(true);
            });
    }
});

export default CreateDatasetView;
