import View from '../view';

import CreateDatasetLicenseInfoPageTemplate from './createDatasetLicenseInfoPage.pug';
import './createDatasetLicenseInfoPage.styl';

// Modal view for dataset license information
const CreateDatasetLicenseInfoWidget = View.extend({
    render: function () {
        this.$el.html(CreateDatasetLicenseInfoPageTemplate()).girderModal(this);
        return this;
    }
});

export default CreateDatasetLicenseInfoWidget;
