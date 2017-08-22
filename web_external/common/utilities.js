import $ from 'jquery';
import _ from 'underscore';

import AlertDialogTemplate from './alertDialog.pug';

/**
 * Miscellaneous utility functions.
 */

/**
 * Show an alert dialog with a single button.
 * @param [text] The text to display.
 * @param [buttonText] The text for the button.
 * @param [buttonClass] Class string to apply to the button.
 * @param [escapedHtml] If you want to render the text as HTML rather than
 *        plain text, set this to true to acknowledge that you have escaped any
 *        user-created data within the text to prevent XSS exploits.
 * @param callback Callback function called when the user clicks the button.
 */
const showAlertDialog = function (params) {
    params = _.extend({
        text: '',
        buttonText: 'OK',
        buttonClass: 'btn-primary',
        escapedHtml: false
    }, params);

    let container = $('#g-dialog-container');
    container
        .html(AlertDialogTemplate({
            params: params
        }))
        .girderModal(false)
        .on('hidden.bs.modal', () => {
            if (params.callback) {
                params.callback();
            }
        });

    let el = container.find('.modal-body>p');
    if (params.escapedHtml) {
        el.html(params.text);
    } else {
        el.text(params.text);
    }

    $('#isic-alert-dialog-button')
        .off('click')
        .click(() => {
            container.modal('hide');
        });
};

export {showAlertDialog};
