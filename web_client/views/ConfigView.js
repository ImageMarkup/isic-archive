import events from 'girder/events';
import PluginConfigBreadcrumbWidget from 'girder/views/widgets/PluginConfigBreadcrumbWidget';
import {restRequest} from 'girder/rest';
import View from 'girder/views/View';

import ConfigViewTemplate from '../templates/configView.pug';

const ConfigView = View.extend({
    events: {
        'submit #isic-config-form': function (event) {
            event.preventDefault();
            this.$('#isic-config-error-message').empty();
            this._saveSettings([{
                key: 'isic.demo_mode',
                value: this.$('#isic-config-demo-mode').prop('checked')
            }, {
                key: 'isic.zip_upload_user_access_key_id',
                value: this.$('#isic-config-zip-upload-user-access-key-id').val().trim()
            }, {
                key: 'isic.zip_upload_user_secret_access_key',
                value: this.$('#isic-config-zip-upload-user-secret-access-key').val().trim()
            }, {
                key: 'isic.zip_upload_s3_bucket_name',
                value: this.$('#isic-config-zip-upload-s3-bucket-name').val().trim()
            }, {
                key: 'isic.zip_upload_role_arn',
                value: this.$('#isic-config-zip-upload-role-arn').val().trim()
            }, {
                key: 'isic.zip_upload_assume_role_duration_seconds',
                value: this.$('#isic-config-zip-upload-assume-role-duration-seconds').val().trim()
            }]);
        }
    },
    initialize: function () {
        restRequest({
            type: 'GET',
            path: 'system/setting',
            data: {
                list: JSON.stringify([
                    'isic.demo_mode',
                    'isic.zip_upload_user_access_key_id',
                    'isic.zip_upload_user_secret_access_key',
                    'isic.zip_upload_s3_bucket_name',
                    'isic.zip_upload_role_arn',
                    'isic.zip_upload_assume_role_duration_seconds'
                ])
            }
        }).done((resp) => {
            this.render();
            this.$('#isic-config-demo-mode').prop(
                'checked',
                resp['isic.demo_mode']
            );
            this.$('#isic-config-zip-upload-user-access-key-id').val(
                resp['isic.zip_upload_user_access_key_id']);
            this.$('#isic-config-zip-upload-user-secret-access-key').val(
                resp['isic.zip_upload_user_secret_access_key']);
            this.$('#isic-config-zip-upload-s3-bucket-name').val(
                resp['isic.zip_upload_s3_bucket_name']);
            this.$('#isic-config-zip-upload-role-arn').val(
                resp['isic.zip_upload_role_arn']);
            this.$('#isic-config-zip-upload-assume-role-duration-seconds').val(
                resp['isic.zip_upload_assume_role_duration_seconds']);
        });
    },

    render: function () {
        this.$el.html(ConfigViewTemplate());
        if (!this.breadcrumb) {
            this.breadcrumb = new PluginConfigBreadcrumbWidget({
                pluginName: 'ISIC Archive',
                el: this.$('.g-config-breadcrumb-container'),
                parentView: this
            }).render();
        }
        return this;
    },

    _saveSettings: function (settings) {
        restRequest({
            type: 'PUT',
            path: 'system/setting',
            data: {
                list: JSON.stringify(settings)
            },
            error: null
        }).done(() => {
            events.trigger('g:alert', {
                icon: 'ok',
                text: 'Settings saved.',
                type: 'success',
                timeout: 4000
            });
        }).fail((resp) => {
            this.$('#isic-config-error-message').text(resp.responseJSON.message);
        });
    }
});

export default ConfigView;
