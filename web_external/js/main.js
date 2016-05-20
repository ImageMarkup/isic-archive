$(function () {
    isic_archive.events.trigger('g:appload.before');
    isic_archive.mainApp = new isic_archive.App({
        el: 'body',
        parentView: null
    });
    isic_archive.events.trigger('g:appload.after');
});
