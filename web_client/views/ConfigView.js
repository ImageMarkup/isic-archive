import events from 'girder/events';
import PluginConfigBreadcrumbWidget from 'girder/views/widgets/PluginConfigBreadcrumbWidget';
import {restRequest} from 'girder/rest';
import View from 'girder/views/View';

import ConfigViewTemplate from '../templates/configView.jade';

var ConfigView = View.extend({
    events: {
        'submit #isic-config-form': function (event) {
            event.preventDefault();
            this.$('#isic-config-error-message').empty();
            this._saveSettings([{
                key: 'isic.demo_mode',
                value: this.$('#isic-config-demo-mode').prop('checked')
            }]);
        }
    },
    initialize: function () {
        restRequest({
            type: 'GET',
            path: 'system/setting',
            data: {
                list: JSON.stringify([
                    'isic.demo_mode'
                ])
            }
        }).done(_.bind(function (resp) {
            this.render();
            this.$('#isic-config-demo-mode').prop(
                'checked',
                resp['isic.demo_mode']
            );
        }, this));
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
        }).done(_.bind(function () {
            events.trigger('g:alert', {
                icon: 'ok',
                text: 'Settings saved.',
                type: 'success',
                timeout: 4000
            });
        }, this)).error(_.bind(function (resp) {
            this.$('#isic-config-error-message').text(
                resp.responseJSON.message
            );
        }, this));
    }
});

export default ConfigView;
