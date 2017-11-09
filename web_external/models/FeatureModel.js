import Backbone from 'backbone';

const FeatureModel = Backbone.Model.extend({
    idAttribute: 'id',

    name: function () {
        return this.get('name');
    }
});

const SelectFeatureModel = FeatureModel.extend({
});

const SuperpixelFeatureModel = FeatureModel.extend({
});

export default FeatureModel;
export {
    SelectFeatureModel,
    SuperpixelFeatureModel
};
