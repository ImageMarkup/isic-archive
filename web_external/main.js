import $ from 'jquery';

import events from 'girder/events';

import IsicApp from './app.js';

$(() => {
    events.trigger('g:appload.before');
    var app = new IsicApp({
        el: 'body',
        parentView: null
    });
    events.trigger('g:appload.after', app);
});
