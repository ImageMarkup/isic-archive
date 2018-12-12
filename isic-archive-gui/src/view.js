import GirderView from 'girder/views/View';
import {formatDate, DATE_SECOND} from 'girder/misc';

const View = GirderView.extend({
    formatDate: function (date) {
        return formatDate(date, DATE_SECOND);
    }
});

export default View;
