import Backbone from 'backbone';

import {getCurrentUser} from '@girder/core/auth';

import View from '../view';
import {showAlertDialog} from '../common/utilities';
import router from '../router';

import CreateDatasetRequestTemplate from './createDatasetRequest.pug';

const CreateDatasetRequestView = View.extend({
    events: {
        'submit #isic-dataset-form': function (event) {
            event.preventDefault();
            this.$('#isic-dataset-submit').girderEnable(false);

            getCurrentUser().setCanCreateDataset()
                .done((resp) => {
                    // Refresh page
                    Backbone.history.loadUrl();
                })
                .fail((resp) => {
                    // Display notification and route to index
                    showAlertDialog({
                        text: resp.message,
                        callback: () => {
                            router.navigate('', {trigger: true});
                        }
                    });
                });
        }
    },

    initialize: function (settings) {
        this.render();
    },

    render: function () {
        this.$el.html(CreateDatasetRequestTemplate());

        return this;
    }
});

export default CreateDatasetRequestView;
