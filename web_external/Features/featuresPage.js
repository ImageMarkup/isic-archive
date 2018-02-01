import FeatureCollection from '../collections/FeatureCollection';
import View from '../view';

import FeaturesPageTemplate from './featuresPage.pug';

const FeaturesPage = View.extend({
    initialize: function (settings) {
        // TODO: maybe pass in the collection, to allow this to render arbitrary sets of features (for a Study)
        this.collection = FeatureCollection.fromMasterFeatures();
        this.render();
    },

    render: function () {
        this.$el.html(FeaturesPageTemplate({
            features: this.collection
        }));

        return this;
    }
});

export default FeaturesPage;
