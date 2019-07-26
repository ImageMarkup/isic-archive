import $ from 'jquery';
import * as Sentry from '@sentry/browser';

import events from '@girder/core/events';

import IsicApp from './app.js';

const sentryDsn = process.env.VUE_APP_SENTRY_DSN;

Sentry.init({ dsn: sentryDsn, release: COMMITHASH });

$(() => {
    events.trigger('g:appload.before');
    const app = new IsicApp({
        el: 'body',
        parentView: null
    });
    events.trigger('g:appload.after', app);
});
