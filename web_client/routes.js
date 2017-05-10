import events from 'girder/events';
import {exposePluginConfig} from 'girder/utilities/PluginUtils';
import router from 'girder/router';

exposePluginConfig('isic_archive', 'plugins/isic_archive/config');

import ConfigView from './views/ConfigView';
router.route('plugins/isic_archive/config', 'isicConfig', function () {
    events.trigger('g:navigateTo', ConfigView);
});
