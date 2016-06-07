isic.views.StudyView = isic.View.extend({
    initialize: function (settings) {
        girder.cancelRestRequests('fetch');

        this.study = settings.study;

        var promises = [];

        // TODO: Add way to detect collection fetch error. On error, set
        // collection to null and reject promise.

        var usersDeferred = $.Deferred();
        promises.push(usersDeferred.promise());
        this.users = new girder.collections.UserCollection();
        this.users.altUrl = 'study/' + this.study.id + '/user';
        this.users.once('g:changed', function () {
            usersDeferred.resolve();
        }, this).fetch();

        var featuresetDeferred = $.Deferred();
        promises.push(featuresetDeferred.promise());
        this.featureset = new isic.models.FeaturesetModel({
            _id: this.study.get('featuresetId')
        }).once('g:fetched', function () {
            featuresetDeferred.resolve();
        }, this).fetch();

        var imagesDeferred = $.Deferred();
        promises.push(imagesDeferred.promise());
        this.images = new isic.collections.ImageCollection();
        this.images.altUrl = 'study/' + this.study.id + '/image';
        this.images.once('g:changed', function () {
            imagesDeferred.resolve();
        }, this).fetch();

        var segmentationsDeferred = $.Deferred();
        promises.push(segmentationsDeferred.promise());
        this.segmentations = new isic.collections.SegmentationCollection();
        this.segmentations.altUrl = 'study/' + this.study.id + '/segmentation';
        this.segmentations.once('g:changed', function () {
            segmentationsDeferred.resolve();
        }, this).fetch();

        $.when.apply($, promises).done(_.bind(function () {
            this.render();
        }, this)).fail(_.bind(function () {
            this.render();
        }, this));
    },

    render: function () {
        this.$el.html(isic.templates.studyPage({
            study: this.study,
            users: this.users,
            featureset: this.featureset,
            images: this.images,
            segmentations: this.segmentations
        }));

        return this;
    }
});
