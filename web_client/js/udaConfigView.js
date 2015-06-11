/*global _, girder*/

girder.views.uda_ConfigView = girder.View.extend({
    events: {
        'submit #uda-config-form': function (event) {
            'use strict';
            event.preventDefault();
            this.$('#uda-config-error-message').empty();
            this._saveSettings([{
                key: 'uda.demo_mode',
                value: this.$('#uda-config-demo-mode').prop('checked')
            }]);
        }
    },
    initialize: function () {
        'use strict';
        girder.restRequest({
            type: 'GET',
            path: 'system/setting',
            data: {
                list: JSON.stringify([
                    'uda.demo_mode'
                ])
            }
        }).done(_.bind(function (resp) {
            this.render();
            this.$('#uda-config-demo-mode').prop(
                'checked',
                resp['uda.demo_mode']
            );
        }, this));
    },

    render: function () {
        'use strict';
        this.$el.html(girder.templates.udaConfig());
        if (!this.breadcrumb) {
            this.breadcrumb = new girder.views.PluginConfigBreadcrumbWidget({
                pluginName: 'UDA 2 Archive',
                el: this.$('.g-config-breadcrumb-container'),
                parentView: this
            }).render();
        }
        return this;
    },

    _saveSettings: function (settings) {
        'use strict';
        girder.restRequest({
            type: 'PUT',
            path: 'system/setting',
            data: {
                list: JSON.stringify(settings)
            },
            error: null
        }).done(_.bind(function () {
            girder.events.trigger('g:alert', {
                icon: 'ok',
                text: 'Settings saved.',
                type: 'success',
                timeout: 4000
            });
        }, this)).error(_.bind(function (resp) {
            this.$('#uda-config-error-message').text(
                resp.responseJSON.message
            );
        }, this));
    }
});

girder.router.route('plugins/uda/config', 'udaConfig', function () {
    'use strict';
    girder.events.trigger('g:navigateTo', girder.views.uda_ConfigView);
});

girder.exposePluginConfig('uda', 'plugins/uda/config');
