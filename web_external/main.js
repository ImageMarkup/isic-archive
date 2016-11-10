$(function () {
    isic.events.trigger('g:appload.before');
    isic.mainApp = new isic.App({
        el: 'body',
        parentView: null
    });
    isic.events.trigger('g:appload.after');
});
