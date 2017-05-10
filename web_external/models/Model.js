import Backbone from 'backbone';

import GirderModel from 'girder/models/Model';

var Model = GirderModel.extend({
    urlRoot: function () {
        return this.resourceName;
    },

    // "GirderModel.destroy" doesn't trigger many of the proper Backbone events
    destroy: Backbone.Model.prototype.destroy
});

export default Model;
