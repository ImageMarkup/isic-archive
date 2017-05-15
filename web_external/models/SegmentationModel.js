import Model from './Model';
import UserModel from './UserModel';

const SegmentationModel = Model.extend({
    resourceName: 'segmentation',

    creator: function () {
        return new UserModel(this.get('creator'));
    }
});

export default SegmentationModel;
