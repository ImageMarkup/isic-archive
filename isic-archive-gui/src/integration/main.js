import $ from 'jquery';

import events from '@girder/core/events';

import IsicApp from './app.js';

$(() => {
    events.trigger('g:appload.before');
    const app = new IsicApp({
        el: 'body',
        parentView: null
    });
    events.trigger('g:appload.after', app);
});
