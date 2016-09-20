girder.views.isic_ConfigView = girder.View.extend({
    events: {
        'submit #isic-config-form': function (event) {
            'use strict';
            event.preventDefault();
            this.$('#isic-config-error-message').empty();
            this._saveSettings([{
                key: 'uda.demo_mode',
                value: this.$('#isic-config-demo-mode').prop('checked')
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
            this.$('#isic-config-demo-mode').prop(
                'checked',
                resp['uda.demo_mode']
            );
        }, this));
    },

    render: function () {
        'use strict';
        this.$el.html(girder.templates.isicConfig());
        if (!this.breadcrumb) {
            this.breadcrumb = new girder.views.PluginConfigBreadcrumbWidget({
                pluginName: 'ISIC Archive',
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
            this.$('#isic-config-error-message').text(
                resp.responseJSON.message
            );
        }, this));
    }
});

girder.router.route('plugins/isic/config', 'isicConfig', function () {
    'use strict';
    girder.events.trigger('g:navigateTo', girder.views.isic_ConfigView);
});

girder.exposePluginConfig('isic_archive', 'plugins/isic/config');
