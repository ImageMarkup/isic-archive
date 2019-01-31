import GirderView from '@girder/core/views/View';
import {formatDate, DATE_SECOND} from '@girder/core/misc';

const View = GirderView.extend({
    formatDate: function (date) {
        return formatDate(date, DATE_SECOND);
    }
});

export default View;
