import GirderView from 'girder/views/View';
import {formatDate, DATE_SECOND} from 'girder/misc';
import {apiRoot} from 'girder/rest';

var View = GirderView.extend({
    formatDate: function (date) {
        return formatDate(date, DATE_SECOND);
    },

    // TODO: These should be re-exposed in ISIC (since the API root could end up being different),
    // but put in a better place (since non-Views may want to access these values)
    apiRoot: apiRoot
});

export default View;
