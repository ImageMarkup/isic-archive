import Backbone from 'backbone';

import GirderModel from '@girder/core/models/Model';
import GirderAccessControlledModel from '@girder/core/models/AccessControlledModel';

const patchedMethods = {
    urlRoot: function () {
        return this.resourceName;
    },

    // "GirderModel.destroy" doesn't trigger many of the proper Backbone events
    destroy: Backbone.Model.prototype.destroy
};

const Model = GirderModel.extend(patchedMethods);
const AccessControlledModel = GirderAccessControlledModel.extend(patchedMethods);

export default Model;
export {AccessControlledModel};
