import Backbone from 'backbone';
import 'backbone.select';

import Collection from './Collection';
import ImageModel from '../models/ImageModel';

const ImageCollection = Collection.extend({
    resourceName: 'image',
    model: ImageModel
});

const SelectableImageCollection = ImageCollection.extend({
    initialize: function (models) {
        Backbone.Select.One.applyTo(this, models);
        ImageCollection.prototype.initialize.apply(this, arguments);
    }
});

export default ImageCollection;
export {SelectableImageCollection};
