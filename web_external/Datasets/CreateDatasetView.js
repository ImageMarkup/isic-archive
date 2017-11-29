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
        'click #isic-create-dataset-show-license-info-link': 'showLicenseInfo',
        'change input[name="attribution"]': function (event) {
            // Update attribution name field sensitivity
            const target = $(event.target);
            if (target.val() === 'anonymous') {
                this.$('#isic-create-dataset-attribution-name').girderEnable(false);
            } else {
                this.$('#isic-create-dataset-attribution-name').girderEnable(true);
            }
        },
        'change #isic-create-dataset-license': function (event) {
            // Disable anonymous attribution unless CC-0 license is selected
            const target = $(event.target);
            const anonymous = this.$('#isic-create-dataset-attribution-anonymous');
            if (target.val() === 'CC-0') {
                anonymous.girderEnable(true);
            } else {
                if (anonymous.prop('checked')) {
                    this.$('#isic-create-dataset-attribution-attributed-to').prop('checked', true);
                    this.$('#isic-create-dataset-attribution-attributed-to').change();
                }
                anonymous.girderEnable(false);
            }
        },
        'submit #isic-create-dataset-form': function (event) {
            event.preventDefault();
            this.$('#isic-create-dataset-submit').girderEnable(false);

            const name = this.$('#isic-create-dataset-name').val();
            const description = this.$('#isic-create-dataset-description').val();
            const owner = this.$('#isic-create-dataset-owner').val();
            const license = this.$('#isic-create-dataset-license').val();
            const anonymous = this.$('#isic-create-dataset-attribution-anonymous').prop('checked');
            const attribution = this.$('#isic-create-dataset-attribution-name').val();

            this.dataset
                .set({
                    name: name,
                    description: description,
                    owner: owner,
                    license: license,
                    attribution: (anonymous ? 'Anonymous' : attribution)
                })
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
    },

    initialize: function (settings) {
        this.dataset = new DatasetModel();

        this.render();
    },

    render: function () {
        this.$el.html(CreateDatasetTemplate());

        this.$('input#isic-create-dataset-name').focus();

        return this;
    },

    showLicenseInfo: function () {
        if (!this.licenseInfoWidget) {
            this.licenseInfoWidget = new CreateDatasetLicenseInfoWidget({
                el: $('#g-dialog-container'),
                parentView: this
            });
        }
        this.licenseInfoWidget.render();
    }
});

export default CreateDatasetView;
