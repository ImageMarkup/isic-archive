import Model from './Model';
import UserModel from './UserModel';

var SegmentationModel = Model.extend({
    resourceName: 'segmentation',

    creator: function () {
        return new UserModel(this.get('creator'));
    }
});

export default SegmentationModel;
