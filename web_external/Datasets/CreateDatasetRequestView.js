import Backbone from 'backbone';

import {getCurrentUser} from 'girder/auth';

import View from '../view';
import {showAlertDialog} from '../common/utilities';
import router from '../router';

import CreateDatasetRequestTemplate from './createDatasetRequest.pug';

var CreateDatasetRequestView = View.extend({
    events: {
        'submit #isic-dataset-form': function (event) {
            event.preventDefault();
            this.$('#isic-dataset-submit').prop('disabled', true);

            getCurrentUser().setCanCreateDataset(
                // Success callback
                function (resp) {
                    // Refresh page
                    Backbone.history.loadUrl();
                },
                // Failure (or request pending) callback
                function (resp) {
                    // Display notification and route to index
                    showAlertDialog({
                        text: resp.message,
                        callback: function () {
                            router.navigate('', {trigger: true});
                        }
                    });
                }
            );
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
