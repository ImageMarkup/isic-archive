import View from '../../view';

import TermsOfUseWidgetTemplate from './termsOfUseWidget.pug';
import './termsOfUseWidget.styl';

const TermsOfUseWidget = View.extend({
    render: function () {
        this.$el.html(TermsOfUseWidgetTemplate());
        return this;
    }
});

export default TermsOfUseWidget;
