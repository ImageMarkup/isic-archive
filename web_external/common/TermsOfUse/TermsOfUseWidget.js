import View from '../../view';

import TermsOfUseWidgetTemplate from './termsOfUseWidget.pug';
import './termsOfUseWidget.styl';

var TermsOfUseWidget = View.extend({
    render: function () {
        this.$el.html(TermsOfUseWidgetTemplate());
    }
});

export default TermsOfUseWidget;
