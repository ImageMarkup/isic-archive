isic.Model = girder.Model.extend({
    urlRoot: function () {
        return this.resourceName;
    },

    // "girder.Model.destroy" doesn't trigger many of the proper Backbone events
    destroy: Backbone.Model.prototype.destroy
});
